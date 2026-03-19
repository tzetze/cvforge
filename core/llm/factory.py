"""
LLM provider factory for creating and managing LLM providers.

This module provides a factory for creating LLM providers based on configuration,
allowing easy switching between different backends.
"""

from typing import Dict, Any, Optional
from core.llm.base import LLMProvider, LLMError
from core.llm.claude_provider import ClaudeProvider
from core.llm.ollama_provider import OllamaProvider


class LLMProviderFactory:
    """
    Factory for creating LLM providers.
    
    Supports multiple provider types and allows easy switching between them.
    """
    
    # Registry of available provider types
    PROVIDERS = {
        "claude": ClaudeProvider,
        "ollama": OllamaProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any]) -> LLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_type: Type of provider ("claude", "ollama")
            config: Provider configuration
            
        Returns:
            LLMProvider instance
            
        Raises:
            LLMError: If provider type is not supported or creation fails
        """
        provider_type = provider_type.lower()
        
        if provider_type not in cls.PROVIDERS:
            available = ", ".join(cls.PROVIDERS.keys())
            raise LLMError(
                f"Unsupported provider type: {provider_type}. "
                f"Available providers: {available}"
            )
        
        provider_class = cls.PROVIDERS[provider_type]
        
        try:
            return provider_class(config)
        except Exception as e:
            raise LLMError(f"Failed to create {provider_type} provider: {e}")
    
    @classmethod
    def create_from_settings(
        cls,
        settings: Dict[str, Any],
        provider_name: Optional[str] = None
    ) -> LLMProvider:
        """
        Create an LLM provider from settings configuration.
        
        Args:
            settings: Settings dict with 'llm' configuration
            provider_name: Optional provider name to use (uses default if not specified)
            
        Returns:
            LLMProvider instance
            
        Raises:
            LLMError: If configuration is invalid or provider creation fails
        """
        if "llm" not in settings:
            raise LLMError("No 'llm' configuration found in settings")
        
        llm_config = settings["llm"]
        
        # Get provider name
        if provider_name is None:
            provider_name = llm_config.get("default_provider")
            if not provider_name:
                raise LLMError("No default_provider specified in LLM configuration")
        
        # Get provider configuration
        providers = llm_config.get("providers", {})
        if provider_name not in providers:
            available = ", ".join(providers.keys())
            raise LLMError(
                f"Provider '{provider_name}' not found in configuration. "
                f"Available providers: {available}"
            )
        
        provider_config = providers[provider_name]
        
        # Get provider type
        provider_type = provider_config.get("type")
        if not provider_type:
            raise LLMError(
                f"No 'type' specified for provider '{provider_name}'"
            )
        
        return cls.create_provider(provider_type, provider_config)
    
    @classmethod
    def list_available_providers(cls) -> list[str]:
        """
        List all available provider types.
        
        Returns:
            List of provider type names
        """
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def register_provider(cls, provider_type: str, provider_class: type) -> None:
        """
        Register a custom provider type.
        
        Args:
            provider_type: Name for the provider type
            provider_class: Provider class (must inherit from LLMProvider)
            
        Raises:
            LLMError: If provider_class is not a valid LLMProvider subclass
        """
        if not issubclass(provider_class, LLMProvider):
            raise LLMError(
                f"Provider class must inherit from LLMProvider, "
                f"got {provider_class.__name__}"
            )
        
        cls.PROVIDERS[provider_type.lower()] = provider_class


class LLMManager:
    """
    Manager for LLM providers with caching and easy access.
    
    This class provides a convenient interface for working with multiple
    LLM providers, with automatic caching and provider switching.
    """
    
    def __init__(self, settings: Dict[str, Any]):
        """
        Initialize the LLM manager.
        
        Args:
            settings: Settings dict with 'llm' configuration
        """
        self.settings = settings
        self._providers: Dict[str, LLMProvider] = {}
        self._default_provider_name = settings.get("llm", {}).get("default_provider")
    
    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """
        Get an LLM provider instance.
        
        Args:
            provider_name: Optional provider name (uses default if not specified)
            
        Returns:
            LLMProvider instance
            
        Raises:
            LLMError: If provider cannot be created
        """
        # Use default if not specified
        if provider_name is None:
            provider_name = self._default_provider_name
            if not provider_name:
                raise LLMError("No default provider configured")
        
        # Return cached provider if available
        if provider_name in self._providers:
            return self._providers[provider_name]
        
        # Create new provider
        provider = LLMProviderFactory.create_from_settings(
            self.settings,
            provider_name
        )
        
        # Cache it
        self._providers[provider_name] = provider
        
        return provider
    
    def get_default_provider(self) -> LLMProvider:
        """
        Get the default LLM provider.
        
        Returns:
            LLMProvider instance
        """
        return self.get_provider()
    
    def list_configured_providers(self) -> list[str]:
        """
        List all configured provider names.
        
        Returns:
            List of provider names from configuration
        """
        return list(self.settings.get("llm", {}).get("providers", {}).keys())
    
    def clear_cache(self) -> None:
        """Clear the provider cache."""
        self._providers.clear()
    
    def set_default_provider(self, provider_name: str) -> None:
        """
        Set the default provider.
        
        Args:
            provider_name: Name of provider to use as default
            
        Raises:
            LLMError: If provider is not configured
        """
        providers = self.settings.get("llm", {}).get("providers", {})
        if provider_name not in providers:
            available = ", ".join(providers.keys())
            raise LLMError(
                f"Provider '{provider_name}' not found. "
                f"Available: {available}"
            )
        
        self._default_provider_name = provider_name
        if "llm" in self.settings:
            self.settings["llm"]["default_provider"] = provider_name


