"""
Ollama provider implementation.

This module implements the LLM provider interface for local Ollama models.
"""

import requests
from typing import Optional, Dict, Any, List

from core.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMInvalidResponseError,
)


class OllamaProvider(LLMProvider):
    """
    Ollama provider implementation.
    
    Supports local Ollama models (Llama, Mistral, CodeLlama, etc.).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Ollama provider.
        
        Args:
            config: Configuration dict with 'base_url', 'model', etc.
        """
        super().__init__(config)
        
        self.base_url = config.get("base_url", "http://localhost:11434")
        if not self.base_url.startswith("http"):
            self.base_url = f"http://{self.base_url}"
        
        # Remove trailing slash
        self.base_url = self.base_url.rstrip("/")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response from Ollama.
        
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
            
            # Add system message if provided
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            # Build request payload
            payload = {
                "model": self.model,
                "messages": full_messages,
                "stream": False,
                "options": {
                    "temperature": temp,
                    "num_predict": tokens,
                }
            }
            
            # Make API call
            url = f"{self.base_url}/api/chat"
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
            )
            
            # Check for errors
            if response.status_code != 200:
                raise LLMError(
                    f"Ollama API returned status {response.status_code}: {response.text}"
                )
            
            # Parse response
            data = response.json()
            
            if "message" not in data or "content" not in data["message"]:
                raise LLMInvalidResponseError(
                    f"Invalid response from Ollama: {data}"
                )
            
            content = data["message"]["content"]
            
            # Build usage info if available
            usage = None
            if "prompt_eval_count" in data and "eval_count" in data:
                usage = {
                    "input_tokens": data.get("prompt_eval_count", 0),
                    "output_tokens": data.get("eval_count", 0),
                }
            
            # Build metadata
            metadata = {
                "model": data.get("model", self.model),
                "done": data.get("done", False),
                "total_duration": data.get("total_duration"),
                "load_duration": data.get("load_duration"),
                "prompt_eval_duration": data.get("prompt_eval_duration"),
                "eval_duration": data.get("eval_duration"),
            }
            
            return LLMResponse(
                content=content,
                model=data.get("model", self.model),
                usage=usage,
                metadata=metadata,
            )
            
        except requests.exceptions.ConnectionError as e:
            raise LLMConnectionError(
                f"Failed to connect to Ollama at {self.base_url}: {e}. "
                f"Make sure Ollama is running."
            )
        except requests.exceptions.Timeout as e:
            raise LLMTimeoutError(f"Ollama request timed out: {e}")
        except requests.exceptions.RequestException as e:
            raise LLMError(f"Ollama request failed: {e}")
        except (KeyError, ValueError) as e:
            raise LLMInvalidResponseError(f"Failed to parse Ollama response: {e}")
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            raise LLMError(f"Unexpected error calling Ollama: {e}")
    
    def is_available(self) -> bool:
        """
        Check if Ollama is available and the model is loaded.
        
        Returns:
            True if provider is available, False otherwise
        """
        try:
            # Check if Ollama is running
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            
            if response.status_code != 200:
                return False
            
            # Check if the model exists
            data = response.json()
            models = data.get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # Check if our model is in the list (exact match or prefix match)
            for model_name in model_names:
                if model_name == self.model or model_name.startswith(f"{self.model}:"):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def list_available_models(self) -> List[str]:
        """
        List all available models in Ollama.
        
        Returns:
            List of model names
            
        Raises:
            LLMConnectionError: If connection fails
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            
            if response.status_code != 200:
                raise LLMConnectionError(
                    f"Failed to list models: status {response.status_code}"
                )
            
            data = response.json()
            models = data.get("models", [])
            return [m.get("name", "") for m in models if m.get("name")]
            
        except requests.exceptions.ConnectionError as e:
            raise LLMConnectionError(
                f"Failed to connect to Ollama at {self.base_url}: {e}"
            )
        except Exception as e:
            raise LLMError(f"Failed to list models: {e}")
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        return f"OllamaProvider(model={self.model}, base_url={self.base_url})"
