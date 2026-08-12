"""
Model Registry for LLM Gateway

This module implements a registry for managing LLM providers and models.
It stores provider information, model capabilities, and allows dynamic provider registration.
"""
from typing import Dict, List, Optional, Type
from .base import BaseProvider, ProviderType, ModelInfo, ModelCapabilities
from .openai_provider import OpenAIProvider
from .provider import OllamaProvider

class ModelRegistry:
    """
    Registry for LLM providers and models
    
    Manages:
    - Provider registration
    - Model information storage
    - Provider instantiation
    - Model lookup by capabilities
    """
    
    def __init__(self):
        self._providers: Dict[ProviderType, Type[BaseProvider]] = {}
        self._models: Dict[str, ModelInfo] = {}
        self._instances: Dict[str, BaseProvider] = {}
        self._register_default_providers()
    
    def _register_default_providers(self):
        """Register built-in providers"""
        self.register_provider(ProviderType.OPENAI_COMPATIBLE, OpenAIProvider)
        self.register_provider(ProviderType.OLLAMA, OllamaProvider)
    
    def register_provider(self, provider_type: ProviderType, provider_class: Type[BaseProvider]):
        """
        Register a provider class
        
        Args:
            provider_type: Type of provider
            provider_class: Class implementing BaseProvider
        """
        self._providers[provider_type] = provider_class
    
    def register_model(self, model_info: ModelInfo):
        """
        Register a model in the registry
        
        Args:
            model_info: Information about the model
        """
        self._models[model_info.model_id] = model_info
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get model information by model ID
        
        Args:
            model_id: Model identifier
            
        Returns:
            ModelInfo if found, None otherwise
        """
        return self._models.get(model_id)
    
    def list_models(self, provider_type: Optional[ProviderType] = None) -> List[ModelInfo]:
        """
        List all registered models
        
        Args:
            provider_type: Optional filter by provider type
            
        Returns:
            List of ModelInfo objects
        """
        if provider_type:
            return [model for model in self._models.values() 
                   if model.provider == provider_type]
        return list(self._models.values())
    
    def get_provider_instance(self, model_id: str, **kwargs) -> BaseProvider:
        """
        Get or create a provider instance for a model
        
        Args:
            model_id: Model identifier
            **kwargs: Additional arguments for provider initialization
            
        Returns:
            BaseProvider instance
        """
        model_info = self.get_model_info(model_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found in registry")
        
        # Create instance key
        instance_key = f"{model_id}_{hash(str(kwargs))}"
        
        # Return existing instance if available
        if instance_key in self._instances:
            return self._instances[instance_key]
        
        # Create new instance
        provider_class = self._providers[model_info.provider]
        instance = provider_class(model=model_info.model_id, **kwargs)
        self._instances[instance_key] = instance
        return instance
    
    def find_models_by_capabilities(self, 
                                  supports_streaming: bool = None,
                                  supports_tools: bool = None,
                                  supports_embeddings: bool = None,
                                  min_context_size: int = None) -> List[ModelInfo]:
        """
        Find models by capabilities
        
        Args:
            supports_streaming: Filter by streaming support
            supports_tools: Filter by tool support
            supports_embeddings: Filter by embedding support
            min_context_size: Minimum context size required
            
        Returns:
            List of matching ModelInfo objects
        """
        results = []
        for model in self._models.values():
            if supports_streaming is not None and model.capabilities.supports_streaming != supports_streaming:
                continue
            if supports_tools is not None and model.capabilities.supports_tools != supports_tools:
                continue
            if supports_embeddings is not None and model.capabilities.supports_embeddings != supports_embeddings:
                continue
            if min_context_size is not None and model.context_size < min_context_size:
                continue
            results.append(model)
        return results
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all provider instances
        
        Returns:
            Dictionary mapping model_id to health status
        """
        results = {}
        for instance_key, instance in self._instances.items():
            try:
                health = await instance.health_check()
                results[instance_key] = health.healthy
            except Exception:
                results[instance_key] = False
        return results
    
    async def close_all(self):
        """Close all provider instances"""
        for instance in self._instances.values():
            await instance.close()
        self._instances.clear()


# Global registry instance
model_registry = ModelRegistry()

# Pre-register common models
def initialize_default_models():
    """Initialize the registry with common models"""
    # OpenAI models
    model_registry.register_model(ModelInfo(
        provider=ProviderType.OPENAI_COMPATIBLE,
        model_id="gpt-4",
        display_name="GPT-4",
        capabilities=ModelCapabilities(
            supports_streaming=True,
            supports_tools=True,
            supports_vision=True,
            supports_embeddings=True,
            max_context_tokens=16384,
            max_output_tokens=8192
        ),
        context_size=16384,
        cost_per_1k_input_tokens=0.03,
        cost_per_1k_output_tokens=0.06,
        is_default=True
    ))
    
    model_registry.register_model(ModelInfo(
        provider=ProviderType.OPENAI_COMPATIBLE,
        model_id="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        capabilities=ModelCapabilities(
            supports_streaming=True,
            supports_tools=True,
            supports_vision=False,
            supports_embeddings=True,
            max_context_tokens=4096,
            max_output_tokens=2048
        ),
        context_size=4096,
        cost_per_1k_input_tokens=0.0015,
        cost_per_1k_output_tokens=0.002,
        is_default=False
    ))

    model_registry.register_model(ModelInfo(
        provider=ProviderType.OPENAI_COMPATIBLE,
        model_id="text-embedding-3-small",
        display_name="OpenAI text-embedding-3-small",
        capabilities=ModelCapabilities(
            supports_streaming=False,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=True,
            max_context_tokens=8192,
            max_output_tokens=0
        ),
        context_size=8192,
        cost_per_1k_input_tokens=0.00002,
        cost_per_1k_output_tokens=0.0,
        is_default=True
    ))
    
    # Ollama models (common ones)
    model_registry.register_model(ModelInfo(
        provider=ProviderType.OLLAMA,
        model_id="llama2",
        display_name="Llama 2",
        capabilities=ModelCapabilities(
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=True,
            max_context_tokens=4096,
            max_output_tokens=2048
        ),
        context_size=4096,
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        is_default=False
    ))

    model_registry.register_model(ModelInfo(
        provider=ProviderType.OLLAMA,
        model_id="nomic-embed-text",
        display_name="Nomic Embed Text",
        capabilities=ModelCapabilities(
            supports_streaming=False,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=True,
            max_context_tokens=8192,
            max_output_tokens=0
        ),
        context_size=8192,
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        is_default=False
    ))
    
    model_registry.register_model(ModelInfo(
        provider=ProviderType.OLLAMA,
        model_id="mistral",
        display_name="Mistral",
        capabilities=ModelCapabilities(
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            max_context_tokens=8192,
            max_output_tokens=2048
        ),
        context_size=8192,
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        is_default=False
    ))

# Initialize default models on import
initialize_default_models()