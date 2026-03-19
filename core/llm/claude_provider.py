"""
Claude API provider implementation.

This module implements the LLM provider interface for Anthropic's Claude API.
"""

import os
from typing import Optional, Dict, Any, List

try:
    from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError, APITimeoutError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

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


class ClaudeProvider(LLMProvider):
    """
    Claude API provider implementation.
    
    Supports Claude 3 models (Opus, Sonnet, Haiku) via Anthropic's API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Claude provider.
        
        Args:
            config: Configuration dict with 'api_key', 'model', etc.
            
        Raises:
            LLMError: If Anthropic library is not installed
        """
        super().__init__(config)
        
        if not ANTHROPIC_AVAILABLE:
            raise LLMError(
                "Anthropic library not installed. "
                "Install with: pip install anthropic"
            )
        
        self.api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise LLMAuthenticationError(
                "Claude API key not found. Set 'api_key' in config or "
                "ANTHROPIC_API_KEY environment variable."
            )
        
        self.client = Anthropic(api_key=self.api_key)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response from Claude.
        
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
        messages = [{"role": "user", "content": prompt}]
        
        return self.generate_with_messages(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
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
        try:
            # Use provided values or fall back to config defaults
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temp,
                "max_tokens": tokens,
            }
            
            # Add system prompt if provided
            if system_prompt:
                request_params["system"] = system_prompt
            
            # Make API call
            response = self.client.messages.create(**request_params)
            
            # Extract content
            content = ""
            if response.content:
                # Claude returns a list of content blocks
                content = "".join(
                    block.text for block in response.content
                    if hasattr(block, "text")
                )
            
            # Build usage info
            usage = None
            if hasattr(response, "usage"):
                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
            
            # Build metadata
            metadata = {
                "model": response.model,
                "stop_reason": response.stop_reason if hasattr(response, "stop_reason") else None,
                "id": response.id if hasattr(response, "id") else None,
            }
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                metadata=metadata,
            )
            
        except APIConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to Claude API: {e}")
        except RateLimitError as e:
            raise LLMRateLimitError(f"Claude API rate limit exceeded: {e}")
        except APITimeoutError as e:
            raise LLMTimeoutError(f"Claude API request timed out: {e}")
        except APIError as e:
            if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                raise LLMAuthenticationError(f"Claude API authentication failed: {e}")
            raise LLMError(f"Claude API error: {e}")
        except Exception as e:
            raise LLMError(f"Unexpected error calling Claude API: {e}")
    
    def is_available(self) -> bool:
        """
        Check if Claude API is available and configured correctly.
        
        Returns:
            True if provider is available, False otherwise
        """
        if not ANTHROPIC_AVAILABLE:
            return False
        
        if not self.api_key:
            return False
        
        try:
            # Try a minimal API call to verify connectivity
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
            )
            return True
        except Exception:
            return False
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        return f"ClaudeProvider(model={self.model})"

