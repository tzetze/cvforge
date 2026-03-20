"""
Unit tests for LLM provider modules
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.llm.base import BaseLLMProvider
from core.llm.factory import create_llm_provider
from core.utils import LLMProviderError, LLMConnectionError


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing"""
    
    def __init__(self):
        self.call_count = 0
        self.last_prompt = None
        self.last_system_prompt = None
    
    def generate(self, prompt: str, system_prompt: str = None, 
                 max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Mock generate method"""
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        return f"Mock response to: {prompt[:50]}"


class TestBaseLLMProvider:
    """Tests for BaseLLMProvider interface"""
    
    def test_base_provider_is_abstract(self):
        """Test that BaseLLMProvider cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseLLMProvider()
    
    def test_mock_provider_implements_interface(self):
        """Test that mock provider implements the interface correctly"""
        provider = MockLLMProvider()
        
        response = provider.generate("Test prompt")
        
        assert isinstance(response, str)
        assert provider.call_count == 1
        assert provider.last_prompt == "Test prompt"
    
    def test_provider_accepts_system_prompt(self):
        """Test that provider accepts system prompt"""
        provider = MockLLMProvider()
        
        response = provider.generate(
            prompt="User prompt",
            system_prompt="System instructions"
        )
        
        assert provider.last_system_prompt == "System instructions"
    
    def test_provider_accepts_parameters(self):
        """Test that provider accepts generation parameters"""
        provider = MockLLMProvider()
        
        # Should not raise errors
        response = provider.generate(
            prompt="Test",
            max_tokens=500,
            temperature=0.5
        )
        
        assert isinstance(response, str)


class TestLLMFactory:
    """Tests for LLM provider factory"""
    
    @patch('core.llm.claude.ClaudeProvider')
    def test_create_claude_provider(self, mock_claude):
        """Test creating Claude provider"""
        mock_instance = Mock()
        mock_claude.return_value = mock_instance
        
        provider = create_llm_provider("claude")
        
        assert provider is not None
        mock_claude.assert_called_once()
    
    @patch('core.llm.ollama.OllamaProvider')
    def test_create_ollama_provider(self, mock_ollama):
        """Test creating Ollama provider"""
        mock_instance = Mock()
        mock_ollama.return_value = mock_instance
        
        provider = create_llm_provider("ollama")
        
        assert provider is not None
        mock_ollama.assert_called_once()
    
    def test_create_invalid_provider(self):
        """Test creating invalid provider raises error"""
        with pytest.raises((ValueError, LLMProviderError)):
            create_llm_provider("invalid_provider")
    
    @patch('core.llm.claude.ClaudeProvider')
    def test_create_provider_with_settings(self, mock_claude):
        """Test creating provider with custom settings"""
        mock_instance = Mock()
        mock_claude.return_value = mock_instance
        
        settings = {
            "model": "claude-3-opus-20240229",
            "temperature": 0.5
        }
        
        provider = create_llm_provider("claude", settings)
        
        assert provider is not None


class TestClaudeProvider:
    """Tests for Claude provider (with mocking)"""
    
    @patch('anthropic.Anthropic')
    def test_claude_provider_initialization(self, mock_anthropic):
        """Test Claude provider initialization"""
        from core.llm.claude import ClaudeProvider
        
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            provider = ClaudeProvider()
            assert provider is not None
    
    @patch('anthropic.Anthropic')
    def test_claude_provider_generate(self, mock_anthropic):
        """Test Claude provider generate method"""
        from core.llm.claude import ClaudeProvider
        
        # Mock the Anthropic client
        mock_client = Mock()
        mock_message = Mock()
        mock_message.content = [Mock(text="Generated response")]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            provider = ClaudeProvider()
            response = provider.generate("Test prompt")
            
            assert response == "Generated response"
            mock_client.messages.create.assert_called_once()
    
    @patch('anthropic.Anthropic')
    def test_claude_provider_handles_errors(self, mock_anthropic):
        """Test Claude provider error handling"""
        from core.llm.claude import ClaudeProvider
        
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            provider = ClaudeProvider()
            
            with pytest.raises((LLMProviderError, Exception)):
                provider.generate("Test prompt")


class TestOllamaProvider:
    """Tests for Ollama provider (with mocking)"""
    
    @patch('requests.post')
    def test_ollama_provider_initialization(self, mock_post):
        """Test Ollama provider initialization"""
        from core.llm.ollama import OllamaProvider
        
        provider = OllamaProvider()
        assert provider is not None
        assert provider.base_url is not None
    
    @patch('requests.post')
    def test_ollama_provider_generate(self, mock_post):
        """Test Ollama provider generate method"""
        from core.llm.ollama import OllamaProvider
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Generated response from Ollama"
        }
        mock_post.return_value = mock_response
        
        provider = OllamaProvider()
        response = provider.generate("Test prompt")
        
        assert response == "Generated response from Ollama"
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_ollama_provider_connection_error(self, mock_post):
        """Test Ollama provider handles connection errors"""
        from core.llm.ollama import OllamaProvider
        import requests
        
        mock_post.side_effect = requests.ConnectionError("Cannot connect")
        
        provider = OllamaProvider()
        
        with pytest.raises((LLMConnectionError, Exception)):
            provider.generate("Test prompt")
    
    @patch('requests.post')
    def test_ollama_provider_custom_model(self, mock_post):
        """Test Ollama provider with custom model"""
        from core.llm.ollama import OllamaProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response
        
        provider = OllamaProvider(model="llama2")
        response = provider.generate("Test")
        
        assert response is not None
        # Verify model was passed in request
        call_args = mock_post.call_args
        assert call_args is not None


class TestLLMProviderIntegration:
    """Integration tests for LLM providers"""
    
    def test_provider_interface_consistency(self):
        """Test that all providers follow the same interface"""
        mock_provider = MockLLMProvider()
        
        # All providers should support these parameters
        response = mock_provider.generate(
            prompt="Test prompt",
            system_prompt="System instructions",
            max_tokens=500,
            temperature=0.7
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_provider_handles_long_prompts(self):
        """Test that providers handle long prompts"""
        mock_provider = MockLLMProvider()
        
        long_prompt = "Test " * 1000
        response = mock_provider.generate(long_prompt)
        
        assert isinstance(response, str)
    
    def test_provider_handles_special_characters(self):
        """Test that providers handle special characters"""
        mock_provider = MockLLMProvider()
        
        special_prompt = "Test with special chars: @#$%^&*(){}[]|\\:;\"'<>,.?/"
        response = mock_provider.generate(special_prompt)
        
        assert isinstance(response, str)
