"""
Abstract base class for LLM providers.

This module defines the interface that all LLM providers must implement,
allowing for easy switching between different LLM backends (Claude, Ollama, etc.).
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers (Claude, Ollama, etc.) must implement this interface
    to ensure consistent behavior across different backends.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM provider.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.model = config.get("model", "")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout", 60)
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt/message
            system_prompt: Optional system prompt to set context
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            LLMResponse object containing the generated text and metadata
            
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @abstractmethod
    def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response using a conversation history.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            system_prompt: Optional system prompt to set context
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            LLMResponse object containing the generated text and metadata
            
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM provider is available and configured correctly.
        
        Returns:
            True if provider is available, False otherwise
        """
        pass
    
    def get_model_name(self) -> str:
        """Get the model name being used."""
        return self.model
    
    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration."""
        return self.config.copy()


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM provider fails."""
    pass


class LLMAuthenticationError(LLMError):
    """Raised when authentication with LLM provider fails."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when request times out."""
    pass


class LLMInvalidResponseError(LLMError):
    """Raised when LLM returns an invalid response."""
    pass

