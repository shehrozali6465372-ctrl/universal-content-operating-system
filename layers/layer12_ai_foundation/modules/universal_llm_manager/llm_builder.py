"""LLMBuilder — Fluent builder for LLMManager."""
from __future__ import annotations
from typing import Any, Optional
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_config import LLMConfig
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_manager import LLMManager

class LLMBuilder:
    def __init__(self) -> None:
        self._config = LLMConfig()
    def provider(self, name: str) -> "LLMBuilder":
        self._config.default_provider = name; return self
    def model(self, name: str) -> "LLMBuilder":
        self._config.default_model = name; return self
    def temperature(self, temp: float) -> "LLMBuilder":
        self._config.default_temperature = temp; return self
    def max_tokens(self, tokens: int) -> "LLMBuilder":
        self._config.default_max_tokens = tokens; return self
    def budget(self, amount: float) -> "LLMBuilder":
        self._config.budget_limit = amount; return self
    def enable_cache(self) -> "LLMBuilder":
        self._config.enable_cache = True; return self
    def enable_streaming(self) -> "LLMBuilder":
        self._config.enable_streaming = True; return self
    def build(self) -> LLMManager:
        return LLMManager(self._config)
