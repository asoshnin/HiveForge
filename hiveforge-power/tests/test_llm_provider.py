"""
Unit tests for LLMProvider abstraction.

Tests all provider paths (KIRO native, Vertex AI, OpenAI, None) and fallback chain.
"""

import asyncio
import json
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from hiveforge.steering.llm.provider import LLMProvider, ProviderType, LLMConfig


class TestLLMConfig:
    """Tests for LLMConfig dataclass"""
    
    def test_llm_config_defaults(self):
        """Test LLMConfig with default values"""
        config = LLMConfig(provider_type=ProviderType.NONE)
        
        assert config.provider_type == ProviderType.NONE
        assert config.api_key is None
        assert config.project_id is None
        assert config.model == "gpt-4"
        assert config.temperature == 0.1
        assert config.max_tokens == 2000
    
    def test_llm_config_custom_values(self):
        """Test LLMConfig with custom values"""
        config = LLMConfig(
            provider_type=ProviderType.OPENAI,
            api_key="test-key",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=1000
        )
        
        assert config.provider_type == ProviderType.OPENAI
        assert config.api_key == "test-key"
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000


class TestLLMProviderInit:
    """Tests for LLMProvider initialization"""
    
    def test_init_with_ctx(self):
        """Test initialization with KIRO context"""
        mock_ctx = MagicMock()
        provider = LLMProvider(ctx=mock_ctx)
        
        assert provider.ctx == mock_ctx
        assert provider.primary_provider == ProviderType.KIRO_NATIVE
    
    def test_init_without_ctx(self):
        """Test initialization without KIRO context"""
        provider = LLMProvider(ctx=None)
        
        assert provider.ctx is None
        assert provider.primary_provider in [ProviderType.NONE, ProviderType.VERTEX_AI, ProviderType.OPENAI]
    
    @patch.dict(os.environ, {"HIVEFORGE_LLM_PROVIDER": "vertex", "GOOGLE_CLOUD_PROJECT": "test-project"})
    def test_init_with_vertex_env_var(self):
        """Test initialization with Vertex AI environment variable"""
        provider = LLMProvider(ctx=None)
        
        assert provider.config.provider_type == ProviderType.VERTEX_AI
        assert provider.config.project_id == "test-project"
    
    @patch.dict(os.environ, {"HIVEFORGE_LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"})
    def test_init_with_openai_env_var(self):
        """Test initialization with OpenAI environment variable"""
        provider = LLMProvider(ctx=None)
        
        assert provider.config.provider_type == ProviderType.OPENAI
        assert provider.config.api_key == "test-key"


class TestLLMProviderConfigLoading:
    """Tests for configuration loading"""
    
    @patch.dict(os.environ, {}, clear=True)
    @patch("pathlib.Path.exists", return_value=False)
    def test_load_config_defaults(self, mock_exists):
        """Test loading config with defaults (no env vars, no file)"""
        provider = LLMProvider(ctx=None)
        
        assert provider.config.provider_type == ProviderType.NONE
    
    @patch.dict(os.environ, {"HIVEFORGE_LLM_PROVIDER": "vertex", "GOOGLE_CLOUD_PROJECT": "my-project"})
    def test_load_config_from_env_vertex(self):
        """Test loading Vertex AI config from environment variables"""
        provider = LLMProvider(ctx=None)
        
        assert provider.config.provider_type == ProviderType.VERTEX_AI
        assert provider.config.project_id == "my-project"
    
    @patch.dict(os.environ, {"HIVEFORGE_LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test123"})
    def test_load_config_from_env_openai(self):
        """Test loading OpenAI config from environment variables"""
        provider = LLMProvider(ctx=None)
        
        assert provider.config.provider_type == ProviderType.OPENAI
        assert provider.config.api_key == "sk-test123"
    
    @patch.dict(os.environ, {}, clear=True)
    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data='{"provider_type": "openai", "api_key": "file-key"}')
    def test_load_config_from_file(self, mock_file, mock_exists):
        """Test loading config from ~/.hiveforge/llm_config.json"""
        provider = LLMProvider(ctx=None)
        
        assert provider.config.provider_type == ProviderType.OPENAI
        assert provider.config.api_key == "file-key"
    
    @patch.dict(os.environ, {}, clear=True)
    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data='invalid json')
    def test_load_config_from_invalid_file(self, mock_file, mock_exists):
        """Test loading config from invalid JSON file falls back to defaults"""
        provider = LLMProvider(ctx=None)
        
        assert provider.config.provider_type == ProviderType.NONE


class TestLLMProviderAvailability:
    """Tests for is_available() method"""
    
    def test_is_available_with_kiro_ctx(self):
        """Test availability with KIRO context"""
        mock_ctx = MagicMock()
        provider = LLMProvider(ctx=mock_ctx)
        
        assert provider.is_available() is True
    
    def test_is_available_without_ctx(self):
        """Test availability without any provider"""
        provider = LLMProvider(ctx=None)
        provider.config.provider_type = ProviderType.NONE
        provider.primary_provider = ProviderType.NONE
        
        assert provider.is_available() is False
    
    @patch("hiveforge.steering.llm.provider.LLMProvider._check_vertex_ai_available", return_value=True)
    def test_is_available_with_vertex(self, mock_check):
        """Test availability with Vertex AI"""
        provider = LLMProvider(ctx=None)
        provider.primary_provider = ProviderType.VERTEX_AI
        
        assert provider.is_available() is True
    
    @patch("hiveforge.steering.llm.provider.LLMProvider._check_openai_available", return_value=True)
    def test_is_available_with_openai(self, mock_check):
        """Test availability with OpenAI"""
        provider = LLMProvider(ctx=None)
        provider.primary_provider = ProviderType.OPENAI
        
        assert provider.is_available() is True


class TestKIRONativeCalls:
    """Tests for KIRO native LLM calls"""
    
    @pytest.mark.asyncio
    async def test_call_kiro_native_success(self):
        """Test successful KIRO native call"""
        mock_ctx = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated content"
        mock_ctx.sample = AsyncMock(return_value=mock_response)
        
        provider = LLMProvider(ctx=mock_ctx)
        result = await provider._call_kiro_native(
            system_prompt="You are a helper",
            user_prompt="Generate content",
            max_tokens=1000
        )
        
        assert result == "Generated content"
        mock_ctx.sample.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_kiro_native_no_ctx(self):
        """Test KIRO native call without context"""
        provider = LLMProvider(ctx=None)
        result = await provider._call_kiro_native(
            system_prompt="You are a helper",
            user_prompt="Generate content",
            max_tokens=1000
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_call_kiro_native_failure(self):
        """Test KIRO native call failure"""
        mock_ctx = MagicMock()
        mock_ctx.sample = AsyncMock(side_effect=Exception("API error"))
        
        provider = LLMProvider(ctx=mock_ctx)
        
        with pytest.raises(Exception, match="API error"):
            await provider._call_kiro_native(
                system_prompt="You are a helper",
                user_prompt="Generate content",
                max_tokens=1000
            )


class TestVertexAICalls:
    """Tests for Vertex AI calls"""
    
    @pytest.mark.asyncio
    @patch("hiveforge.steering.llm.provider.aiplatform")
    @patch("hiveforge.steering.llm.provider.GenerativeModel")
    @patch("hiveforge.steering.llm.provider.GenerationConfig")
    @patch("asyncio.to_thread")
    async def test_call_vertex_ai_success(self, mock_to_thread, mock_gen_config, mock_model_class, mock_aiplatform):
        """Test successful Vertex AI call"""
        mock_response = MagicMock()
        mock_response.text = "Vertex generated content"
        mock_to_thread.return_value = mock_response
        
        provider = LLMProvider(ctx=None)
        provider.config.provider_type = ProviderType.VERTEX_AI
        provider.config.project_id = "test-project"
        
        result = await provider._call_vertex_ai(
            system_prompt="You are a helper",
            user_prompt="Generate content",
            max_tokens=1000,
            temperature=0.3,
            json_mode=False
        )
        
        assert result == "Vertex generated content"
        mock_aiplatform.init.assert_called_once_with(project="test-project")
    
    @pytest.mark.asyncio
    @patch("hiveforge.steering.llm.provider.aiplatform", side_effect=ImportError("No module"))
    async def test_call_vertex_ai_import_error(self, mock_aiplatform):
        """Test Vertex AI call with import error"""
        provider = LLMProvider(ctx=None)
        provider.config.provider_type = ProviderType.VERTEX_AI
        provider.config.project_id = "test-project"
        
        with pytest.raises(ImportError):
            await provider._call_vertex_ai(
                system_prompt="You are a helper",
                user_prompt="Generate content",
                max_tokens=1000,
                temperature=0.3,
                json_mode=False
            )


class TestOpenAICalls:
    """Tests for OpenAI calls"""
    
    @pytest.mark.asyncio
    @patch("hiveforge.steering.llm.provider.AsyncOpenAI")
    async def test_call_openai_success(self, mock_openai_class):
        """Test successful OpenAI call"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OpenAI generated content"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        
        provider = LLMProvider(ctx=None)
        provider.config.provider_type = ProviderType.OPENAI
        provider.config.api_key = "test-key"
        
        result = await provider._call_openai(
            system_prompt="You are a helper",
            user_prompt="Generate content",
            max_tokens=1000,
            temperature=0.3,
            json_mode=False
        )
        
        assert result == "OpenAI generated content"
        mock_openai_class.assert_called_once_with(api_key="test-key")
    
    @pytest.mark.asyncio
    @patch("hiveforge.steering.llm.provider.AsyncOpenAI")
    async def test_call_openai_with_json_mode(self, mock_openai_class):
        """Test OpenAI call with JSON mode"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"key": "value"}'
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        
        provider = LLMProvider(ctx=None)
        provider.config.provider_type = ProviderType.OPENAI
        provider.config.api_key = "test-key"
        
        result = await provider._call_openai(
            system_prompt="You are a helper",
            user_prompt="Generate JSON",
            max_tokens=1000,
            temperature=0.3,
            json_mode=True
        )
        
        assert result == '{"key": "value"}'
        
        # Verify JSON mode was requested
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}


class TestFallbackChain:
    """Tests for fallback chain logic"""
    
    @pytest.mark.asyncio
    async def test_complete_kiro_success(self):
        """Test complete() with successful KIRO native call"""
        mock_ctx = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "KIRO content"
        mock_ctx.sample = AsyncMock(return_value=mock_response)
        
        provider = LLMProvider(ctx=mock_ctx)
        result = await provider.complete(
            system_prompt="You are a helper",
            user_prompt="Generate content"
        )
        
        assert result == "KIRO content"
    
    @pytest.mark.asyncio
    @patch("hiveforge.steering.llm.provider.AsyncOpenAI")
    async def test_complete_fallback_to_openai(self, mock_openai_class):
        """Test complete() falls back to OpenAI when KIRO fails"""
        mock_ctx = MagicMock()
        mock_ctx.sample = AsyncMock(side_effect=Exception("KIRO error"))
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OpenAI fallback content"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        
        provider = LLMProvider(ctx=mock_ctx)
        provider.config.api_key = "test-key"
        
        result = await provider.complete(
            system_prompt="You are a helper",
            user_prompt="Generate content"
        )
        
        assert result == "OpenAI fallback content"
    
    @pytest.mark.asyncio
    async def test_complete_all_providers_fail(self):
        """Test complete() returns None when all providers fail"""
        mock_ctx = MagicMock()
        mock_ctx.sample = AsyncMock(side_effect=Exception("KIRO error"))
        
        provider = LLMProvider(ctx=mock_ctx)
        provider.config.provider_type = ProviderType.NONE
        
        result = await provider.complete(
            system_prompt="You are a helper",
            user_prompt="Generate content"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_complete_no_provider_available(self):
        """Test complete() with no provider available"""
        provider = LLMProvider(ctx=None)
        provider.config.provider_type = ProviderType.NONE
        provider.primary_provider = ProviderType.NONE
        
        result = await provider.complete(
            system_prompt="You are a helper",
            user_prompt="Generate content"
        )
        
        assert result is None


class TestProviderChecks:
    """Tests for provider availability checks"""
    
    @patch("hiveforge.steering.llm.provider.aiplatform")
    def test_check_vertex_ai_available_with_project(self, mock_aiplatform):
        """Test Vertex AI availability check with project ID"""
        provider = LLMProvider(ctx=None)
        provider.config.project_id = "test-project"
        
        assert provider._check_vertex_ai_available() is True
    
    @patch("hiveforge.steering.llm.provider.aiplatform")
    def test_check_vertex_ai_available_without_project(self, mock_aiplatform):
        """Test Vertex AI availability check without project ID"""
        provider = LLMProvider(ctx=None)
        provider.config.project_id = None
        
        assert provider._check_vertex_ai_available() is False
    
    def test_check_vertex_ai_import_error(self):
        """Test Vertex AI availability check with import error"""
        provider = LLMProvider(ctx=None)
        provider.config.project_id = "test-project"
        
        with patch("hiveforge.steering.llm.provider.aiplatform", side_effect=ImportError()):
            assert provider._check_vertex_ai_available() is False
    
    @patch("hiveforge.steering.llm.provider.AsyncOpenAI")
    def test_check_openai_available_with_key(self, mock_openai):
        """Test OpenAI availability check with API key"""
        provider = LLMProvider(ctx=None)
        provider.config.api_key = "test-key"
        
        assert provider._check_openai_available() is True
    
    @patch("hiveforge.steering.llm.provider.AsyncOpenAI")
    def test_check_openai_available_without_key(self, mock_openai):
        """Test OpenAI availability check without API key"""
        provider = LLMProvider(ctx=None)
        provider.config.api_key = None
        
        assert provider._check_openai_available() is False
    
    def test_check_openai_import_error(self):
        """Test OpenAI availability check with import error"""
        provider = LLMProvider(ctx=None)
        provider.config.api_key = "test-key"
        
        with patch("hiveforge.steering.llm.provider.AsyncOpenAI", side_effect=ImportError()):
            assert provider._check_openai_available() is False
