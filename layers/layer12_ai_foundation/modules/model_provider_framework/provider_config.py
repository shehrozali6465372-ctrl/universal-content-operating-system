"""provider_config.py — Provider configuration."""
from __future__ import annotations
from typing import Any, Dict


class ProviderConfig:
    """Configuration for a specific provider."""

    __slots__ = ("name", "api_key", "base_url", "default_model", "temperature",
                 "max_tokens", "timeout", "max_retries", "enable_cache",
                 "enable_streaming", "metadata")

    def __init__(self, name: str = "", api_key: str = "") -> None:
        self.name = name
        self.api_key = api_key
        self.base_url: str = ""
        self.default_model: str = ""
        self.temperature: float = 0.7
        self.max_tokens: int = 4096
        self.timeout: float = 60.0
        self.max_retries: int = 3
        self.enable_cache: bool = True
        self.enable_streaming: bool = False
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__ if s != "metadata"}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        c = cls()
        for k, v in data.items():
            if hasattr(c, k):
                setattr(c, k, v)
        return c
