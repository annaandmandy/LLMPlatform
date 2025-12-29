"""
Provider factory for creating LLM provider instances.

Centralized registry and instantiation of all LLM providers.
"""

import logging
from typing import Dict, Type, Optional

from app.providers.base import BaseLLMProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.google_provider import GoogleProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.core.config import is_provider_available

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Factory for creating LLM provider instances.
    
    Maintains a registry of all available providers and handles instantiation.
    """
    
    # Registry of provider classes
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "openrouter": OpenRouterProvider,
        "openrouter_perplexity": OpenRouterProvider,  # Alias
        "openrouter_grok": OpenRouterProvider,  # Alias
    }
    
    # Cache of instantiated providers (singleton pattern)
    _instances: Dict[str, BaseLLMProvider] = {}
    
    @classmethod
    def get_provider(cls, provider_name: str, api_key: Optional[str] = None) -> BaseLLMProvider:
        """
        Get a provider instance by name.
        
        Args:
            provider_name: Name of the provider (e.g., 'openai', 'anthropic')
            api_key: Optional API key override
            
        Returns:
            Instantiated provider
            
        Raises:
            ValueError: If provider is unknown or not available
        """
        # Normalize provider name
        provider_name = provider_name.lower().strip()
        
        # Check if provider exists
        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unknown provider: '{provider_name}'. "
                f"Available providers: {available}"
            )
        
        # Check if provider is configured (has API key)
        base_provider = provider_name.split("_")[0]  # Handle openrouter_* aliases
        if not api_key and not is_provider_available(base_provider):
            raise ValueError(
                f"Provider '{provider_name}' is not configured. "
                f"Please set the API key in settings."
            )
        
        # Return cached instance if available (and no custom API key)
        if not api_key and provider_name in cls._instances:
            return cls._instances[provider_name]
        
        # Create new instance
        provider_class = cls._providers[provider_name]
        instance = provider_class(api_key=api_key)
        
        # Cache if using default API key
        if not api_key:
            cls._instances[provider_name] = instance
        
        logger.info(f"✅ Created {provider_name} provider instance")
        return instance
    
    @classmethod
    def get_all_providers(cls) -> Dict[str, callable]:
        """
        Get dictionary of all provider functions (legacy compatibility).
        
        This returns callable wrappers for backward compatibility with
        the old function-based approach.
        
        Returns:
            Dict mapping provider names to callable functions
        """
        def make_call_fn(provider_name: str):
            """Create a callable wrapper for a provider."""
            async def call_fn(model: str, query: str, system_prompt: Optional[str] = None, **kwargs):
                provider = cls.get_provider(provider_name)
                return await provider.generate(model, query, system_prompt, **kwargs)
            return call_fn
        
        return {
            name: make_call_fn(name)
            for name in ["openai", "anthropic", "google", "openrouter"]
        }
    
    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: Type[BaseLLMProvider]
    ):
        """
        Register a new provider class.
        
        Args:
            name: Provider name
            provider_class: Provider class (must extend BaseLLMProvider)
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise ValueError(
                f"Provider class must extend BaseLLMProvider, "
                f"got {provider_class.__name__}"
            )
        
        cls._providers[name] = provider_class
        logger.info(f"✅ Registered provider: {name}")
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """
        List all registered provider names.
        
        Returns:
            List of provider names
        """
        return list(cls._providers.keys())
    
    @classmethod
    def clear_cache(cls):
        """Clear the provider instance cache."""
        cls._instances.clear()
        logger.info("✅ Provider cache cleared")
