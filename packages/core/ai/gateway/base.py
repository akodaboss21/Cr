"""
LLM Gateway - Base Provider Interface

This module defines the abstract base class that all LLM providers must implement.
The application communicates with LLMGateway, NOT directly with providers.
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ProviderType(str, Enum):
    """Supported LLM provider types"""
    OPENAI_COMPATIBLE = "openai_compatible"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


@dataclass
class ModelCapabilities:
    """Model capabilities and metadata"""
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_vision: bool = False
    supports_embeddings: bool = False
    max_context_tokens: int = 4096
    max_output_tokens: int = 2048


@dataclass
class ModelInfo:
    """Model information for registry"""
    provider: ProviderType
    model_id: str
    display_name: str
    capabilities: ModelCapabilities
    context_size: int
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0
    is_default: bool = False


@dataclass
class CompletionRequest:
    """Standard completion request"""
    messages: List[Dict[str, str]]
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    user: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CompletionResponse:
    """Standard completion response"""
    id: str
    model: str
    content: str
    role: str = "assistant"
    finish_reason: str = "stop"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StreamingChunk:
    """Streaming response chunk"""
    id: str
    model: str
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    is_final: bool = False


@dataclass
class EmbeddingRequest:
    """Embedding request"""
    input: List[str]
    model: str
    user: Optional[str] = None


@dataclass
class EmbeddingResponse:
    """Embedding response"""
    embeddings: List[List[float]]
    model: str
    prompt_tokens: int = 0
    total_tokens: int = 0


@dataclass
class TokenCount:
    """Token count result"""
    prompt_tokens: int
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class HealthCheckResult:
    """Health check result"""
    healthy: bool
    provider: ProviderType
    model: str
    latency_ms: float
    error: Optional[str] = None


class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    Every provider must implement:
    - complete(): Non-streaming completion
    - stream(): Streaming completion
    - embed(): Generate embeddings
    - count_tokens(): Count tokens in text
    - health_check(): Check provider health
    """
    
    def __init__(
        self,
        provider_type: ProviderType,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        **kwargs
    ):
        self.provider_type = provider_type
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None
    
    @property
    @abstractmethod
    def capabilities(self) -> ModelCapabilities:
        """Return model capabilities"""
        pass
    
    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """
        Generate a non-streaming completion.
        
        Args:
            request: CompletionRequest with messages and parameters
            
        Returns:
            CompletionResponse with generated content
        """
        pass
    
    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamingChunk, None]:
        """
        Generate a streaming completion.
        
        Args:
            request: CompletionRequest with messages and parameters
            
        Yields:
            StreamingChunk objects with partial content
        """
        pass
    
    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings for input texts.
        
        Args:
            request: EmbeddingRequest with input texts
            
        Returns:
            EmbeddingResponse with embeddings
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str, model: Optional[str] = None) -> TokenCount:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            model: Optional model override
            
        Returns:
            TokenCount with token counts
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """
        Check provider health.
        
        Returns:
            HealthCheckResult with health status
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close provider connections"""
        pass
    
    def get_model_info(self) -> ModelInfo:
        """Get model information for registry"""
        return ModelInfo(
            provider=self.provider_type,
            model_id=self.model,
            display_name=f"{self.provider_type.value}/{self.model}",
            capabilities=self.capabilities,
            context_size=self.capabilities.max_context_tokens,
        )


class ProviderError(Exception):
    """Base exception for provider errors"""
    def __init__(self, message: str, provider: ProviderType, model: str, original_error: Optional[Exception] = None):
        self.message = message
        self.provider = provider
        self.model = model
        self.original_error = original_error
        super().__init__(f"[{provider.value}/{model}] {message}")


class ProviderTimeoutError(ProviderError):
    """Provider request timeout"""
    pass


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded"""
    pass


class ProviderAuthenticationError(ProviderError):
    """Provider authentication failed"""
    pass


class ProviderUnavailableError(ProviderError):
    """Provider is unavailable"""
    pass


class ProviderInvalidRequestError(ProviderError):
    """Invalid request to provider"""
    pass