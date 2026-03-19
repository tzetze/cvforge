"""
LLM provider module for CVForge.

This module provides a unified interface for working with different LLM providers
(Claude API, Ollama, etc.) with easy configuration and switching.
"""

from core.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMError,
    LLMConnectionError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMInvalidResponseError,
)
from core.llm.claude_provider import ClaudeProvider
from core.llm.ollama_provider import OllamaProvider
from core.llm.factory import LLMProviderFactory, LLMManager

__all__ = [
    # Base classes
    "LLMProvider",
    "LLMResponse",
    # Exceptions
    "LLMError",
    "LLMConnectionError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMInvalidResponseError",
    # Providers
    "ClaudeProvider",
    "OllamaProvider",
    # Factory
    "LLMProviderFactory",
    "LLMManager",
]


