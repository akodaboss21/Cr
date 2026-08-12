"""
OpenAI Compatible Provider Implementation

This provider implements the BaseProvider interface for OpenAI-compatible APIs.
It uses environment variables LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL for configuration.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from .base import (
    BaseProvider,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    HealthCheckResult,
    ModelCapabilities,
    ProviderAuthenticationError,
    ProviderError,
    ProviderInvalidRequestError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderType,
    StreamingChunk,
    TokenCount,
)


class OpenAIProvider(BaseProvider):
    """
    OpenAI-compatible LLM provider implementation.

    Uses environment variables:
    - LLM_BASE_URL: Base URL for OpenAI API
    - LLM_API_KEY: API key for authentication
    - LLM_MODEL: Model identifier
    """

    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(
            provider_type=ProviderType.OPENAI_COMPATIBLE,
            model=model,
            api_key=api_key or os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        )
        self.timeout = kwargs.get("timeout", 60.0)
        self.max_retries = kwargs.get("max_retries", 3)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=headers,
            base_url=self.base_url.rstrip("/") + "/",
        )

    @property
    def capabilities(self) -> ModelCapabilities:
        """Return model capabilities."""
        return ModelCapabilities(
            supports_streaming=True,
            supports_tools=self.model.startswith("gpt-4"),
            supports_vision=False,
            supports_embeddings=True,
            max_context_tokens=16384 if self.model.startswith("gpt-4") else 4096,
            max_output_tokens=8192 if self.model.startswith("gpt-4") else 2048,
        )

    async def _request_with_retries(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(method, url, **kwargs)
                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt, 4))
                    continue
                response.raise_for_status()
                return response
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt == self.max_retries - 1:
                    raise ProviderTimeoutError("OpenAI request timed out", self.provider_type, self.model, exc) from exc
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code if exc.response else 0
                if status_code == 401:
                    raise ProviderAuthenticationError("OpenAI authentication failed", self.provider_type, self.model, exc) from exc
                if status_code == 429:
                    raise ProviderRateLimitError("OpenAI rate limit exceeded", self.provider_type, self.model, exc) from exc
                if status_code in {400, 404}:
                    raise ProviderInvalidRequestError("OpenAI request was invalid", self.provider_type, self.model, exc) from exc
                if status_code >= 500 and attempt < self.max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt, 4))
                    last_error = exc
                    continue
                raise ProviderError("OpenAI request failed", self.provider_type, self.model, exc) from exc
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
                last_error = exc
                if attempt == self.max_retries - 1:
                    raise ProviderUnavailableError("OpenAI provider is unavailable", self.provider_type, self.model, exc) from exc
            except Exception as exc:
                last_error = exc
                if attempt == self.max_retries - 1:
                    raise ProviderError("OpenAI request failed", self.provider_type, self.model, exc) from exc
            if attempt < self.max_retries - 1:
                await asyncio.sleep(min(2 ** attempt, 4))

        if last_error:
            raise ProviderError("OpenAI request failed", self.provider_type, self.model, last_error)
        raise ProviderError("OpenAI request failed", self.provider_type, self.model)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate a non-streaming completion."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "stream": False,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            payload["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            payload["presence_penalty"] = request.presence_penalty
        if request.stop is not None:
            payload["stop"] = request.stop
        if request.tools is not None:
            payload["tools"] = request.tools
        if request.tool_choice is not None:
            payload["tool_choice"] = request.tool_choice
        if request.user is not None:
            payload["user"] = request.user

        response = await self._request_with_retries("POST", "/chat/completions", json=payload)
        data = response.json()
        if not data.get("choices"):
            raise ProviderInvalidRequestError("OpenAI returned no completion choices", self.provider_type, self.model)

        choice = data["choices"][0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))

        usage = data.get("usage", {}) or {}
        return CompletionResponse(
            id=data.get("id", str(uuid.uuid4())),
            model=self.model,
            content=content if isinstance(content, str) else str(content),
            role=message.get("role", "assistant"),
            finish_reason=choice.get("finish_reason", "stop"),
            prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
            completion_tokens=int(usage.get("completion_tokens", 0) or 0),
            total_tokens=int(usage.get("total_tokens", 0) or 0),
            tool_calls=choice.get("tool_calls") or message.get("tool_calls"),
            metadata={"raw_response": data},
        )

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Generate a streaming completion."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "stream": True,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            payload["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            payload["presence_penalty"] = request.presence_penalty
        if request.stop is not None:
            payload["stop"] = request.stop
        if request.tools is not None:
            payload["tools"] = request.tools
        if request.tool_choice is not None:
            payload["tool_choice"] = request.tool_choice
        if request.user is not None:
            payload["user"] = request.user

        try:
            async with self._client.stream("POST", "/chat/completions", json=payload) as response:
                raise_for_status = getattr(response, "raise_for_status", None)
                if callable(raise_for_status):
                    raise_for_status()
                async for raw_line in response.aiter_lines():
                    if not raw_line or not raw_line.startswith("data:"):
                        continue
                    payload_line = raw_line[len("data:"):].strip()
                    if payload_line == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(payload_line)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk_data.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta") or {}
                    content = delta.get("content") or ""
                    role = delta.get("role") or "assistant"
                    finish_reason = choices[0].get("finish_reason")
                    is_final = bool(finish_reason)

                    if content:
                        yield StreamingChunk(
                            id=chunk_data.get("id", str(uuid.uuid4())),
                            model=self.model,
                            content=content,
                            role=role,
                            finish_reason=finish_reason,
                            is_final=is_final,
                        )
                    elif is_final:
                        yield StreamingChunk(
                            id=chunk_data.get("id", str(uuid.uuid4())),
                            model=self.model,
                            content="",
                            role=role,
                            finish_reason=finish_reason,
                            is_final=True,
                        )
        except httpx.HTTPStatusError as exc:
            raise ProviderError("OpenAI streaming failed", self.provider_type, self.model, exc) from exc
        except Exception as exc:
            raise ProviderError("OpenAI streaming failed", self.provider_type, self.model, exc) from exc

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings."""
        payload: Dict[str, Any] = {"input": request.input, "model": self.model}
        if request.user is not None:
            payload["user"] = request.user

        response = await self._request_with_retries("POST", "/embeddings", json=payload)
        data = response.json()
        embeddings: List[List[float]] = []
        for item in data.get("data", []):
            vector = item.get("embedding") or []
            embeddings.append([float(value) for value in vector])

        if not embeddings:
            raise ProviderInvalidRequestError("OpenAI returned no embeddings", self.provider_type, self.model)

        usage = data.get("usage", {}) or {}
        return EmbeddingResponse(
            embeddings=embeddings,
            model=self.model,
            prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
            total_tokens=int(usage.get("total_tokens", 0) or 0),
        )

    async def count_tokens(self, text: str, model: Optional[str] = None) -> TokenCount:
        """Count tokens in text using a local heuristic and fallback to tiktoken."""
        try:
            import tiktoken  # type: ignore

            encoding_name = "cl100k_base"
            target_model = model or self.model
            if target_model.startswith("gpt-3.5") or target_model.startswith("gpt-4"):
                encoding_name = "cl100k_base"
            else:
                encoding_name = "gpt2"
            encoding = tiktoken.get_encoding(encoding_name)
            tokens = encoding.encode(text)
            return TokenCount(prompt_tokens=len(tokens), completion_tokens=0, total_tokens=len(tokens))
        except Exception:
            tokens = len(re.findall(r"\w+|[^\s\w]", text))
            return TokenCount(prompt_tokens=tokens, completion_tokens=0, total_tokens=tokens)

    async def health_check(self) -> HealthCheckResult:
        """Check provider health by hitting a real provider endpoint."""
        start = time.perf_counter()
        last_error: Optional[str] = None
        try:
            response = await self._client.get("/models")
            latency_ms = int((time.perf_counter() - start) * 1000)
            if response.status_code in {200, 401, 403, 404}:
                return HealthCheckResult(
                    healthy=True,
                    provider=self.provider_type,
                    model=self.model,
                    latency_ms=latency_ms,
                )
            last_error = f"status={response.status_code}"
        except Exception as exc:
            last_error = str(exc)

        return HealthCheckResult(
            healthy=False,
            provider=self.provider_type,
            model=self.model,
            latency_ms=int((time.perf_counter() - start) * 1000),
            error=last_error or "provider unreachable",
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
