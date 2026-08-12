import pytest

from packages.core.ai.gateway import LLMGateway
from packages.core.ai.gateway.base import CompletionRequest, EmbeddingRequest, CompletionResponse, EmbeddingResponse, StreamingChunk
from packages.core.ai.gateway.openai_provider import OpenAIProvider


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("request failed")

    def json(self):
        return self._payload


class FakeStreamResponse:
    def __init__(self, lines):
        self._lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def aiter_lines(self):
        for line in self._lines:
            yield line


@pytest.mark.asyncio
async def test_complete_parses_chat_completions(monkeypatch):
    provider = OpenAIProvider(model="gpt-3.5-turbo", api_key="test-key")

    async def fake_request(method, url, **kwargs):
        return FakeResponse(
            {
                "id": "chatcmpl-1",
                "choices": [{"message": {"role": "assistant", "content": "Hello there"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
            }
        )

    monkeypatch.setattr(provider, "_request_with_retries", fake_request)
    request = CompletionRequest(messages=[{"role": "user", "content": "Hi"}], model="gpt-3.5-turbo")

    response = await provider.complete(request)

    assert response.content == "Hello there"
    assert response.prompt_tokens == 5
    assert response.total_tokens == 7


@pytest.mark.asyncio
async def test_stream_yields_sse_chunks(monkeypatch):
    provider = OpenAIProvider(model="gpt-3.5-turbo", api_key="test-key")

    class FakeStreamClient:
        def __init__(self, response):
            self.response = response

        def stream(self, method, url, **kwargs):
            return FakeStreamResponse(["data: {\"id\": \"1\", \"choices\": [{\"delta\": {\"content\": \"Hello\"}}]}", "data: [DONE]"])

    monkeypatch.setattr(provider._client, "stream", FakeStreamClient(None).stream)
    request = CompletionRequest(messages=[{"role": "user", "content": "Hi"}], model="gpt-3.5-turbo")

    chunks = [chunk async for chunk in provider.stream(request)]

    assert len(chunks) == 1
    assert chunks[0].content == "Hello"


@pytest.mark.asyncio
async def test_embed_uses_embeddings_endpoint(monkeypatch):
    provider = OpenAIProvider(model="text-embedding-3-small", api_key="test-key")

    async def fake_request(method, url, **kwargs):
        return FakeResponse(
            {
                "data": [{"embedding": [0.1, 0.2, 0.3]}],
                "usage": {"prompt_tokens": 3, "total_tokens": 3},
            }
        )

    monkeypatch.setattr(provider, "_request_with_retries", fake_request)
    request = EmbeddingRequest(input=["hi"], model="text-embedding-3-small")

    response = await provider.embed(request)

    assert response.embeddings == [[0.1, 0.2, 0.3]]
    assert response.prompt_tokens == 3


@pytest.mark.asyncio
async def test_health_check_pings_provider(monkeypatch):
    provider = OpenAIProvider(model="gpt-3.5-turbo", api_key="test-key")

    async def fake_get(url):
        return FakeResponse({}, status_code=200)

    monkeypatch.setattr(provider._client, "get", fake_get)

    result = await provider.health_check()

    assert result.healthy is True
    assert result.provider.value == "openai_compatible"


@pytest.mark.asyncio
async def test_gateway_complete_and_embed_delegate_to_provider(monkeypatch):
    gateway = LLMGateway(default_model="gpt-3.5-turbo")

    class DummyProvider:
        def __init__(self):
            self.provider_type = "openai_compatible"

        async def complete(self, request):
            return CompletionResponse(id="1", model=request.model, content="ok")

        async def embed(self, request):
            return EmbeddingResponse(embeddings=[[1.0]], model=request.model, prompt_tokens=1, total_tokens=1)

        async def stream(self, request):
            if False:
                yield StreamingChunk(id="1", model=request.model, content="")

        async def health_check(self):
            return None

        async def close(self):
            return None

    provider = DummyProvider()
    monkeypatch.setattr(gateway.registry, "get_provider_instance", lambda model_id, **kwargs: provider)

    completion = await gateway.complete([{"role": "user", "content": "Hi"}], model="gpt-3.5-turbo")
    embedding = await gateway.embed(["Hi"], model="gpt-3.5-turbo")

    assert completion.content == "ok"
    assert embedding.embeddings == [[1.0]]
