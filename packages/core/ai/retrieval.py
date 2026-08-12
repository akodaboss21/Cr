import hashlib
import json
import math
import os
import re
from typing import Any, Dict, List, Optional, Sequence

from packages.core.ai.gateway import LLMGateway


class KnowledgeSearchEngine:
    """Simple RAG retrieval engine with cosine similarity over knowledge embeddings."""

    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        self.llm_gateway = llm_gateway or LLMGateway()

    async def embed_query(self, query: str, organization_id: Optional[str] = None) -> List[float]:
        if not query or not query.strip():
            return []

        try:
            response = await self.llm_gateway.embed(
                texts=[query],
                model=os.getenv("EMBEDDING_MODEL") or os.getenv("LLM_MODEL") or "text-embedding-3-small",
                organization_id=organization_id,
            )
            if response and getattr(response, "embeddings", None):
                return [float(value) for value in response.embeddings[0]]
        except Exception:
            pass

        return self._fallback_embed(query)

    def _fallback_embed(self, text: str) -> List[float]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return []

        dimensions = 256
        vector = [0.0] * dimensions
        for token in tokens:
            index = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dimensions
            vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector)) if sum(value * value for value in vector) else 1.0
        return [value / norm for value in vector]

    def _coerce_embedding(self, raw_value: Any) -> List[float]:
        if isinstance(raw_value, str):
            try:
                parsed = json.loads(raw_value)
                if isinstance(parsed, list):
                    return [float(value) for value in parsed]
            except (TypeError, ValueError):
                return []
        if isinstance(raw_value, (list, tuple)):
            return [float(value) for value in raw_value]
        return []

    async def _embed_entry(self, entry: Dict[str, Any], organization_id: Optional[str] = None) -> List[float]:
        embedding = self._coerce_embedding(entry.get("embedding_vector"))
        if embedding:
            return embedding

        text_parts: List[str] = []
        for key in ("title", "name", "content", "text"):
            value = entry.get(key)
            if isinstance(value, str) and value.strip():
                text_parts.append(value.strip())

        if not text_parts:
            return []

        return await self.embed_query("\n".join(text_parts), organization_id=organization_id)

    def _cosine_similarity(self, left: Sequence[float], right: Sequence[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = sum(float(a) * float(b) for a, b in zip(left, right))
        left_norm = math.sqrt(sum(float(v) * float(v) for v in left))
        right_norm = math.sqrt(sum(float(v) * float(v) for v in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return dot / (left_norm * right_norm)

    async def search(self, query: str, knowledge_entries: Sequence[Dict[str, Any]], organization_id: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        if not query or not knowledge_entries:
            return []

        query_embedding = await self.embed_query(query, organization_id=organization_id)
        if not query_embedding:
            return []

        ranked: List[Dict[str, Any]] = []
        for entry in knowledge_entries:
            embedding = await self._embed_entry(entry, organization_id=organization_id)
            if not embedding:
                continue
            score = self._cosine_similarity(query_embedding, embedding)
            if score <= 0.0:
                continue
            item = dict(entry)
            item["score"] = round(score, 6)
            ranked.append(item)

        ranked.sort(key=lambda item: item.get("score", 0.0), reverse=True)
        return ranked[: max(1, top_k)]
