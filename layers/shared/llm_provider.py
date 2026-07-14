"""
AI Model Abstraction
Common interface for all LLM providers (GPT, Gemini, Claude, etc.)

This allows swapping providers without changing any layer code.
Simply register a new provider via the factory.

Usage:
    provider = LLMFactory.create("openai", api_key="sk-...")
    response = provider.generate("Write a Facebook post about AI")
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMResponse:
    """Standardized response from any LLM provider."""

    __slots__ = ("content", "model", "usage", "latency_ms", "raw")

    def __init__(
        self,
        content: str = "",
        model: str = "",
        usage: Optional[Dict[str, int]] = None,
        latency_ms: float = 0.0,
        raw: Any = None,
    ):
        self.content = content
        self.model = model
        self.usage = usage or {}
        self.latency_ms = latency_ms
        self.raw = raw

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
        }


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    def get_provider_name(self) -> str: ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    def get_models(self) -> List[str]:
        return []

    def calculate_cost(self, response: LLMResponse) -> float:
        return 0.0


class LLMFactory:
    """Factory for creating LLM providers."""

    _providers: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, provider_class: type):
        cls._providers[name] = provider_class

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> BaseLLMProvider:
        if name not in cls._providers:
            raise ValueError(f"Unknown LLM provider: '{name}'. Available: {list(cls._providers.keys())}")
        return cls._providers[name](**kwargs)

    @classmethod
    def get_available_providers(cls) -> List[str]:
        return list(cls._providers.keys())

    @classmethod
    def reset(cls):
        cls._providers.clear()
