"""
LLM Provider abstraction with priority routing:
1. KIRO native (ctx.sample()) - primary for MCP mode
2. Google Vertex AI
3. OpenAI
4. None (fallback to [INFERRED] markers)
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
import asyncio
import json
import logging
import os
from pathlib import Path


class ProviderType(Enum):
    """Available LLM provider types"""
    KIRO_NATIVE = "kiro_native"
    VERTEX_AI = "vertex_ai"
    OPENAI = "openai"
    NONE = "none"


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider_type: ProviderType
    api_key: Optional[str] = None
    project_id: Optional[str] = None  # For Vertex AI
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2000


class LLMProvider:
    """
    Routes LLM calls to available providers with priority:
    1. KIRO native (ctx.sample()) - primary for MCP mode
    2. Google Vertex AI
    3. OpenAI
    4. None (fallback to [INFERRED] markers)
    """
    
    def __init__(self, ctx: Optional[Any] = None):
        """
        Initialize LLMProvider with optional KIRO context.
        
        Args:
            ctx: KIRO context object (available in MCP mode)
        """
        self.ctx = ctx
        self.config = self._load_config()
        self.primary_provider = self._determine_primary_provider()
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> LLMConfig:
        """
        Load configuration from:
        1. Environment variables (highest priority)
        2. ~/.hiveforge/llm_config.json
        3. Defaults
        """
        # Check environment variables first
        if os.getenv("HIVEFORGE_LLM_PROVIDER") == "vertex":
            return LLMConfig(
                provider_type=ProviderType.VERTEX_AI,
                project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
                api_key=os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            )
        elif os.getenv("HIVEFORGE_LLM_PROVIDER") == "openai":
            return LLMConfig(
                provider_type=ProviderType.OPENAI,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        
        # Check config file
        config_path = Path.home() / ".hiveforge" / "llm_config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config_dict = json.load(f)
                    # Convert provider_type string to enum
                    if "provider_type" in config_dict:
                        config_dict["provider_type"] = ProviderType(config_dict["provider_type"])
                    return LLMConfig(**config_dict)
            except Exception as e:
                self.logger.warning(f"Error loading config file: {e}")
        
        # Default: no external provider
        return LLMConfig(provider_type=ProviderType.NONE)
    
    def _determine_primary_provider(self) -> ProviderType:
        """Determine which provider to use based on context and config"""
        if self.ctx is not None:
            return ProviderType.KIRO_NATIVE
        
        if self.config.provider_type != ProviderType.NONE:
            return self.config.provider_type
        
        return ProviderType.NONE
    
    def is_available(self) -> bool:
        """Check if any LLM provider is available and accessible"""
        try:
            if self.primary_provider == ProviderType.KIRO_NATIVE:
                return self.ctx is not None
            elif self.primary_provider == ProviderType.VERTEX_AI:
                return self._check_vertex_ai_available()
            elif self.primary_provider == ProviderType.OPENAI:
                return self._check_openai_available()
            return False
        except Exception as e:
            self.logger.warning(f"Error checking LLM availability: {e}")
            return False
    
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> Optional[str]:
        """
        Call LLM with fallback chain.
        
        Args:
            system_prompt: System instruction for the LLM
            user_prompt: User message/prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            json_mode: Whether to request JSON response format
        
        Returns:
            LLM response string, or None if all providers fail
        """
        try:
            if self.primary_provider == ProviderType.KIRO_NATIVE:
                return await self._call_kiro_native(system_prompt, user_prompt, max_tokens)
            elif self.primary_provider == ProviderType.VERTEX_AI:
                return await self._call_vertex_ai(system_prompt, user_prompt, max_tokens, temperature, json_mode)
            elif self.primary_provider == ProviderType.OPENAI:
                return await self._call_openai(system_prompt, user_prompt, max_tokens, temperature, json_mode)
        except Exception as e:
            self.logger.warning(f"LLM call failed with {self.primary_provider.value}: {e}")
            return await self._fallback_chain(system_prompt, user_prompt, max_tokens, temperature, json_mode)
        
        return None
    
    async def _call_kiro_native(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int
    ) -> Optional[str]:
        """Call KIRO native LLM via ctx.sample()"""
        if self.ctx is None:
            return None
        
        try:
            # ctx.sample() is async in FastMCP
            response = await self.ctx.sample(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                max_tokens=max_tokens
            )
            return response.text
        except Exception as e:
            self.logger.warning(f"KIRO native call failed: {e}")
            raise
    
    async def _call_vertex_ai(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool
    ) -> Optional[str]:
        """Call Google Vertex AI API"""
        try:
            from google.cloud import aiplatform
            from vertexai.generative_models import GenerativeModel, GenerationConfig
            
            # Initialize Vertex AI
            aiplatform.init(project=self.config.project_id)
            
            # Create model instance
            model = GenerativeModel(
                model_name="gemini-pro",
                system_instruction=system_prompt
            )
            
            # Configure generation
            gen_config = GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                response_mime_type="application/json" if json_mode else "text/plain"
            )
            
            # Call model in thread to avoid blocking (Vertex SDK is sync)
            response = await asyncio.to_thread(
                model.generate_content,
                user_prompt,
                generation_config=gen_config
            )
            
            return response.text
        except Exception as e:
            self.logger.warning(f"Vertex AI call failed: {e}")
            raise
    
    async def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool
    ) -> Optional[str]:
        """Call OpenAI API with AsyncOpenAI client"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=self.config.api_key)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            kwargs = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content
        except Exception as e:
            self.logger.warning(f"OpenAI call failed: {e}")
            raise
    
    async def _fallback_chain(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool
    ) -> Optional[str]:
        """Try remaining providers in priority order"""
        providers = [
            (ProviderType.VERTEX_AI, self._call_vertex_ai),
            (ProviderType.OPENAI, self._call_openai)
        ]
        
        for provider_type, call_func in providers:
            if provider_type == self.primary_provider:
                continue  # Already tried
            
            try:
                self.logger.info(f"Falling back to {provider_type.value}")
                return await call_func(system_prompt, user_prompt, max_tokens, temperature, json_mode)
            except Exception as e:
                self.logger.warning(f"Fallback {provider_type.value} failed: {e}")
                continue
        
        return None
    
    def _check_vertex_ai_available(self) -> bool:
        """Check if Vertex AI is configured and accessible"""
        try:
            from google.cloud import aiplatform
            return self.config.project_id is not None
        except ImportError:
            return False
    
    def _check_openai_available(self) -> bool:
        """Check if OpenAI is configured and accessible"""
        try:
            from openai import AsyncOpenAI
            return self.config.api_key is not None
        except ImportError:
            return False
