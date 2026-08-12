"""
Ollama Provider Implementation

This provider implements the BaseProvider interface for Ollama LLM APIs.
It uses environment variables OLLAMA_BASE_URL and OLLAMA_MODEL for configuration.
"""
from typing import AsyncGenerator, List, Optional
from datetime import datetime
import os
import uuid
import httpx
import json
import math
import re
from .base import BaseProvider, ProviderType, CompletionRequest, CompletionResponse, StreamingChunk, TokenCount, HealthCheckResult, ModelCapabilities, EmbeddingRequest, EmbeddingResponse, ProviderError

class OllamaProvider(BaseProvider):
    """
    Ollama LLM provider implementation
    
    Uses environment variables:
    - OLLAMA_BASE_URL: Base URL for Ollama API
    - OLLAMA_MODEL: Model identifier
    """

    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(
            provider_type=ProviderType.OLLAMA,
            model=model,
            api_key=api_key,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        self.timeout = kwargs.get("timeout", 60.0)
        self.max_retries = kwargs.get("max_retries", 3)
        self._client = httpx.AsyncClient(timeout=self.timeout)

    @property
    def capabilities(self) -> ModelCapabilities:
        """Return model capabilities"""
        return ModelCapabilities(
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=True,
            max_context_tokens=32768,
            max_output_tokens=8192
        )

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """
        Generate a non-streaming completion
        """
        try:
            # Prepare the request payload for Ollama
            payload = {
                "model": self.model,
                "prompt": request.messages[-1]["content"] if request.messages else "",
                "stream": False,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens or 2048,
                "stop": request.stop or ["\n"]
            }
            
            async with self._client.post(f"/api/generate", json=payload) as response:
                if response.status_code != 200:
                    raise ProviderError("Ollama completion failed", self.provider_type, self.model, 
                                      f"HTTP {response.status_code}")
                
                result = await response.json()
                return CompletionResponse(
                    id=result.get("response_id", str(uuid4())),
                    model=self.model,
                    content=result.get("response", ""),
                    prompt_tokens=result.get("prompt_tokens", 0),
                    completion_tokens=result.get("token_count", 0),
                    total_tokens=result.get("total_tokens", 0)
                )
        except Exception as e:
            raise ProviderError("Ollama completion failed", self.provider_type, self.model, e)

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamingChunk, None]:
        """
        Generate a streaming completion
        """
        try:
            # Prepare the request payload for Ollama streaming
            payload = {
                "model": self.model,
                "prompt": request.messages[-1]["content"] if request.messages else "",
                "stream": True,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens or 2048,
                "stop": request.stop or ["\n"]
            }
            
            async with self._client.post(f"/api/generate", json=payload) as response:
                if response.status_code != 200:
                    raise ProviderError("Ollama streaming failed", self.provider_type, self.model,
                                      f"HTTP {response.status_code}")
                
                async for chunk in response.aiter_lines():
                    if chunk:
                        # Parse the JSON chunk
                        data = json.loads(chunk)
                        if "response" in data:
                            yield StreamingChunk(
                                id=str(uuid4()),
                                model=self.model,
                                content=data["response"],
                                is_final="done" in data.get("done", False)
                            )
        except Exception as e:
            raise ProviderError("Ollama streaming failed", self.provider_type, self.model, e)

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings using Ollama if available, otherwise fall back to a deterministic local embedding.
        """
        try:
            payload = {"model": self.model, "input": request.input}
            async with self._client.post("/api/embeddings", json=payload) as response:
                if response.status_code == 200:
                    result = await response.json()
                    embeddings = [list(item.get("embedding", [])) for item in result.get("embeddings", [])]
                    if embeddings:
                        return EmbeddingResponse(
                            embeddings=embeddings,
                            model=self.model,
                            prompt_tokens=sum(len(inp) for inp in request.input),
                            total_tokens=sum(len(inp) for inp in request.input),
                        )
        except Exception:
            pass

        embeddings = [self._fallback_embed(text) for text in request.input]
        return EmbeddingResponse(
            embeddings=embeddings,
            model=self.model,
            prompt_tokens=sum(len(inp) for inp in request.input),
            total_tokens=sum(len(inp) for inp in request.input),
        )

    def _fallback_embed(self, text: str) -> List[float]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return []
        counts = {}
        for token in tokens:
            counts[token] = counts.get(token, 0.0) + 1.0
        vector = [counts[token] for token in sorted(counts)]
        if not vector:
            return []
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    async def count_tokens(self, text: str, model: Optional[str] = None) -> TokenCount:
        """
        Count tokens in text
        """
        # Ollama doesn't have direct token counting API
        return TokenCount(
            prompt_tokens=len(text.split()),
            completion_tokens=0,
            total_tokens=len(text.split())
        )

    async def health_check(self) -> HealthCheckResult:
        """
        Check provider health
        """
        try:
            async with self._client.get(f"/api/tags") as response:
                healthy = response.status_code == 200
                return HealthCheckResult(
                    healthy=healthy,
                    provider=self.provider_type,
                    model=self.model,
                    latency_ms=0,
                    error=None if healthy else "Ollama service unreachable"
                )
        except Exception as e:
            return HealthCheckResult(
                healthy=False,
                provider=self.provider_type,
                model=self.model,
                latency_ms=0,
                error=str(e)
            )

    async def close(self) -> None:
        """Close HTTP client"""
        await self._client.aclose()