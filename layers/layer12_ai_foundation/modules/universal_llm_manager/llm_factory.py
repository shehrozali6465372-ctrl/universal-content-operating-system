"""LLMFactory — Create LLM manager instances."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_config import LLMConfig
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_manager import LLMManager

class LLMFactory:
    PRESETS = {
        "development": {"default_provider": "ollama", "default_model": "llama3.1",
                        "budget_limit": 10.0, "enable_cache": True},
        "production": {"default_provider": "openai", "default_model": "gpt-4o-mini",
                       "budget_limit": 100.0, "enable_streaming": True},
        "premium": {"default_provider": "openai", "default_model": "gpt-4o",
                    "budget_limit": 500.0, "enable_streaming": True},
        "budget": {"default_provider": "deepseek", "default_model": "deepseek-chat",
                   "budget_limit": 50.0},
    }
    @classmethod
    def create(cls, preset: str = "production") -> LLMManager:
        config = LLMConfig.from_dict(cls.PRESETS.get(preset, cls.PRESETS["production"]))
        return LLMManager(config)
    @classmethod
    def create_multi_provider(cls) -> LLMManager:
        config = LLMConfig()
        config.default_provider = "openai"
        config.enable_fallback = True
        return LLMManager(config)
    @classmethod
    def get_presets(cls) -> Dict[str, Dict[str, Any]]:
        return dict(cls.PRESETS)
