"""LLMFactory — Create LLM manager instances."""
from __future__ import annotations

from typing import Any, Dict, Optional

from layers.layer12_ai_foundation.modules.model_provider_framework.claude_provider import ClaudeProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.cohere_provider import CohereProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.deepseek_provider import DeepSeekProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.gemini_provider import GeminiProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.grok_provider import GrokProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.mistral_provider import MistralProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.ollama_provider import OllamaProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.openai_provider import OpenAIProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.openrouter_provider import OpenRouterProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import ProviderRequest
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_registry import ProviderRegistry
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_config import LLMConfig
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_manager import LLMManager


class LLMFactory:
    """Create managers wired to real Layer 12 provider adapters."""

    PRESETS = {
        "development": {
            "default_provider": "ollama",
            "default_model": "llama3.1",
            "budget_limit": 10.0,
            "enable_cache": True,
        },
        "production": {
            "default_provider": "deepseek",
            "default_model": "deepseek-flash",
            "budget_limit": 100.0,
            "enable_streaming": False,
        },
        "premium": {
            "default_provider": "openai",
            "default_model": "gpt-5.6-sol",
            "budget_limit": 500.0,
            "enable_streaming": False,
        },
        "budget": {
            "default_provider": "deepseek",
            "default_model": "deepseek-flash",
            "budget_limit": 50.0,
        },
    }

    PROVIDER_TYPES = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        "gemini": GeminiProvider,
        "deepseek": DeepSeekProvider,
        "grok": GrokProvider,
        "mistral": MistralProvider,
        "cohere": CohereProvider,
        "openrouter": OpenRouterProvider,
        "ollama": OllamaProvider,
    }

    @classmethod
    def _create_registry(cls) -> ProviderRegistry:
        registry = ProviderRegistry()
        for provider_cls in cls.PROVIDER_TYPES.values():
            provider = provider_cls({})
            provider.initialize()
            registry.register(provider)
        return registry

    @classmethod
    def _build_generator(cls, registry: ProviderRegistry, config: LLMConfig):
        def generate(**kwargs: Any):
            provider_name = str(kwargs.get("provider") or config.default_provider)
            provider = registry.get(provider_name)
            if provider is None:
                raise RuntimeError(f"Unknown LLM provider: {provider_name}")
            request = ProviderRequest(
                str(kwargs.get("prompt") or ""),
                str(kwargs.get("model") or config.default_model),
                provider_name,
            )
            request.temperature = float(
                kwargs.get("temperature", config.default_temperature)
            )
            request.max_tokens = int(
                kwargs.get("max_tokens", config.default_max_tokens)
            )
            request.system_prompt = str(kwargs.get("system_prompt") or "")
            request.messages = list(kwargs.get("messages") or [])
            if not request.messages and request.prompt:
                request.messages = [{"role": "user", "content": request.prompt}]
            return provider.generate(request)

        return generate

    @classmethod
    def create(cls, preset: str = "production") -> LLMManager:
        config = LLMConfig.from_dict(
            cls.PRESETS.get(preset, cls.PRESETS["production"])
        )
        registry = cls._create_registry()
        return LLMManager(config, generator=cls._build_generator(registry, config))

    @classmethod
    def create_multi_provider(cls) -> LLMManager:
        config = LLMConfig()
        registry = cls._create_registry()
        return LLMManager(config, generator=cls._build_generator(registry, config))

    @classmethod
    def get_presets(cls) -> Dict[str, Dict[str, Any]]:
        return dict(cls.PRESETS)
