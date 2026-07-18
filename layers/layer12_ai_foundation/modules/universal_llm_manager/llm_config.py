"""LLMConfig — Configuration for LLM manager."""
from __future__ import annotations
from typing import Any, Dict, Optional

class LLMConfig:
    __slots__ = ("default_provider", "default_model", "default_temperature",
                 "default_max_tokens", "default_timeout", "max_retries",
                 "enable_cache", "enable_streaming", "enable_cost_tracking",
                 "budget_limit", "metadata")

    def __init__(self) -> None:
        self.default_provider: str = "openai"
        self.default_model: str = "gpt-4o-mini"
        self.default_temperature: float = 0.7
        self.default_max_tokens: int = 4096
        self.default_timeout: float = 60.0
        self.max_retries: int = 3
        self.enable_cache: bool = True
        self.enable_streaming: bool = False
        self.enable_cost_tracking: bool = True
        self.budget_limit: float = 100.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__ if s != "metadata"}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMConfig":
        c = cls()
        for k, v in data.items():
            if hasattr(c, k):
                setattr(c, k, v)
        return c
