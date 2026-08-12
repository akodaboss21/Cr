"""
LLM Gateway - Main Entry Point

This is the main interface that the application uses to interact with LLMs.
It abstracts away provider details and provides a unified API.
"""
from typing import AsyncGenerator, List, Optional, Dict, Any
from datetime import datetime
import time
import uuid
from .base import (
    BaseProvider, ProviderType, CompletionRequest, CompletionResponse,
    StreamingChunk, EmbeddingRequest, EmbeddingResponse, TokenCount,
    HealthCheckResult, ProviderError, ProviderTimeoutError,
    ProviderRateLimitError, ProviderAuthenticationError,
    ProviderUnavailableError, ProviderInvalidRequestError
)
from .registry import model_registry, ModelRegistry
from .openai_provider import OpenAIProvider
from .provider import OllamaProvider

class LLMGateway:
    """
    Main LLM Gateway for the application
    
    The application communicates with LLMGateway, NOT directly with providers.
    This gateway handles:
    - Provider selection and fallback
    - Request routing
    - Cost tracking
    - Error handling and retries
    - Streaming support
    """
    
    def __init__(
        self,
        default_model: str = "gpt-3.5-turbo",
        fallback_models: Optional[List[str]] = None,
        registry: Optional[ModelRegistry] = None,
        enable_cost_tracking: bool = True,
        max_retries: int = 3,
        timeout: float = 60.0
    ):
        self.default_model = default_model
        self.fallback_models = fallback_models or ["gpt-3.5-turbo", "llama2"]
        self.registry = registry or model_registry
        self.enable_cost_tracking = enable_cost_tracking
        self.max_retries = max_retries
        self.timeout = timeout
        self._usage_callbacks: List[callable] = []
    
    def add_usage_callback(self, callback: callable):
        """
        Add a callback for usage tracking
        
        Args:
            callback: Function to call with usage data
        """
        self._usage_callbacks.append(callback)
    
    def _get_provider_type_value(self, provider: Any) -> str:
        if hasattr(provider.provider_type, "value"):
            return provider.provider_type.value
        return str(provider.provider_type)

    def _notify_usage(self, usage_data: Dict[str, Any]):
        """Notify all usage callbacks"""
        for callback in self._usage_callbacks:
            try:
                callback(usage_data)
            except Exception:
                pass  # Don't let usage tracking break the main flow

    def _calculate_cost(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost for a request"""
        model_info = self.registry.get_model_info(model_id)
        if not model_info:
            return 0.0
        
        input_cost = (prompt_tokens / 1000) * model_info.cost_per_1k_input_tokens
        output_cost = (completion_tokens / 1000) * model_info.cost_per_1k_output_tokens
        return input_cost + output_cost

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        organization_id: Optional[str] = None
    ) -> CompletionResponse:
        """
        Generate a completion (non-streaming)
        
        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream (ignored, use stream() method)
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            user: User identifier
            metadata: Additional metadata
            organization_id: Organization ID for cost tracking
            
        Returns:
            CompletionResponse with generated content
        """
        model = model or self.default_model
        request = CompletionRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            tools=tools,
            tool_choice=tool_choice,
            user=user,
            metadata=metadata
        )
        
        return await self._execute_with_fallback(request, organization_id)
    
    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        organization_id: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        """
        Generate a streaming completion
        
        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            user: User identifier
            metadata: Additional metadata
            organization_id: Organization ID for cost tracking
            
        Yields:
            StreamingChunk objects with partial content
        """
        model = model or self.default_model
        request = CompletionRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            tools=tools,
            tool_choice=tool_choice,
            user=user,
            metadata=metadata
        )
        
        async for chunk in self._stream_with_fallback(request, organization_id):
            yield chunk
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        user: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> EmbeddingResponse:
        """
        Generate embeddings for texts
        
        Args:
            texts: List of texts to embed
            model: Model to use (defaults to default_model)
            user: User identifier
            organization_id: Organization ID for cost tracking
            
        Returns:
            EmbeddingResponse with embeddings
        """
        model = model or self.default_model
        request = EmbeddingRequest(
            input=texts,
            model=model,
            user=user
        )
        
        return await self._execute_embedding_with_fallback(request, organization_id)
    
    async def count_tokens(
        self,
        text: str,
        model: Optional[str] = None
    ) -> TokenCount:
        """
        Count tokens in text
        
        Args:
            text: Text to count tokens for
            model: Model to use (defaults to default_model)
            
        Returns:
            TokenCount with token counts
        """
        model = model or self.default_model
        provider = self.registry.get_provider_instance(model)
        return await provider.count_tokens(text, model)
    
    async def health_check(self, model: Optional[str] = None) -> HealthCheckResult:
        """
        Check health of a model
        
        Args:
            model: Model to check (defaults to default_model)
            
        Returns:
            HealthCheckResult with health status
        """
        model = model or self.default_model
        provider = self.registry.get_provider_instance(model)
        return await provider.health_check()
    
    async def _execute_with_fallback(
        self,
        request: CompletionRequest,
        organization_id: Optional[str] = None
    ) -> CompletionResponse:
        """Execute completion with fallback logic"""
        models_to_try = [request.model] + [m for m in self.fallback_models if m != request.model]
        
        last_error = None
        for model in models_to_try:
            try:
                provider = self.registry.get_provider_instance(model)
                start_time = time.time()
                response = await provider.complete(request)
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Track usage
                if self.enable_cost_tracking:
                    cost = self._calculate_cost(model, response.prompt_tokens, response.completion_tokens)
                    usage_data = {
                        "organization_id": organization_id,
                        "provider": self._get_provider_type_value(provider),
                        "model": model,
                        "prompt_tokens": response.prompt_tokens,
                        "completion_tokens": response.completion_tokens,
                        "total_tokens": response.total_tokens,
                        "cost_usd": cost,
                        "duration_ms": duration_ms,
                        "request_id": response.id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    self._notify_usage(usage_data)
                
                return response
                
            except (ProviderTimeoutError, ProviderRateLimitError, ProviderUnavailableError) as e:
                last_error = e
                continue
            except ProviderAuthenticationError as e:
                # Don't fallback on auth errors
                raise
            except ProviderInvalidRequestError as e:
                # Don't fallback on invalid requests
                raise
            except Exception as e:
                last_error = e
                continue
        
        # All models failed
        raise ProviderError(
            f"All models failed. Last error: {last_error}",
            ProviderType.CUSTOM,
            request.model,
            last_error
        )
    
    async def _stream_with_fallback(
        self,
        request: CompletionRequest,
        organization_id: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        """Execute streaming with fallback logic"""
        models_to_try = [request.model] + [m for m in self.fallback_models if m != request.model]
        
        for model in models_to_try:
            try:
                provider = self.registry.get_provider_instance(model)
                start_time = time.time()
                
                async for chunk in provider.stream(request):
                    yield chunk
                
                # Track usage for streaming (approximate)
                if self.enable_cost_tracking:
                    duration_ms = int((time.time() - start_time) * 1000)
                    # We don't have exact token counts for streaming, estimate
                    usage_data = {
                        "organization_id": organization_id,
                        "provider": self._get_provider_type_value(provider),
                        "model": model,
                        "prompt_tokens": 0,  # Would need to count from request
                        "completion_tokens": 0,  # Would need to count from response
                        "total_tokens": 0,
                        "cost_usd": 0.0,
                        "duration_ms": duration_ms,
                        "request_id": str(uuid.uuid4()),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    self._notify_usage(usage_data)
                
                return  # Success, don't try fallbacks
                
            except (ProviderTimeoutError, ProviderRateLimitError, ProviderUnavailableError) as e:
                continue
            except ProviderAuthenticationError as e:
                raise
            except ProviderInvalidRequestError as e:
                raise
            except Exception as e:
                continue
        
        # All models failed
        raise ProviderError(
            f"All models failed for streaming",
            ProviderType.CUSTOM,
            request.model
        )
    
    async def _execute_embedding_with_fallback(
        self,
        request: EmbeddingRequest,
        organization_id: Optional[str] = None
    ) -> EmbeddingResponse:
        """Execute embedding with fallback logic"""
        models_to_try = [request.model] + [m for m in self.fallback_models if m != request.model]
        
        last_error = None
        for model in models_to_try:
            try:
                provider = self.registry.get_provider_instance(model)
                start_time = time.time()
                response = await provider.embed(request)
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Track usage
                if self.enable_cost_tracking:
                    cost = self._calculate_cost(model, response.prompt_tokens, 0)
                    usage_data = {
                        "organization_id": organization_id,
                        "provider": self._get_provider_type_value(provider),
                        "model": model,
                        "prompt_tokens": response.prompt_tokens,
                        "completion_tokens": 0,
                        "total_tokens": response.total_tokens,
                        "cost_usd": cost,
                        "duration_ms": duration_ms,
                        "request_id": str(uuid.uuid4()),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    self._notify_usage(usage_data)
                
                return response
                
            except (ProviderTimeoutError, ProviderRateLimitError, ProviderUnavailableError) as e:
                last_error = e
                continue
            except ProviderAuthenticationError as e:
                raise
            except ProviderInvalidRequestError as e:
                raise
            except Exception as e:
                last_error = e
                continue
        
        raise ProviderError(
            f"All models failed for embeddings. Last error: {last_error}",
            ProviderType.CUSTOM,
            request.model,
            last_error
        )
    
    async def close(self):
        """Close all provider connections"""
        await self.registry.close_all()


# Global gateway instance
llm_gateway = LLMGateway()