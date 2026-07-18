"""provider_factory.py — Factory to create AI provider instances."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import BaseProvider


class ProviderFactory:
    """Factory for creating AI provider instances."""

    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, provider_name: str, provider_class: type) -> None:
        cls._registry[provider_name.lower()] = provider_class

    @classmethod
    def create(cls, provider_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseProvider]:
        key = provider_name.lower()
        if key in cls._registry:
            return cls._registry[key](config)
        return None

    @classmethod
    def get_supported(cls) -> list:
        return list(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()

    @classmethod
    def has_provider(cls, name: str) -> bool:
        return name.lower() in cls._registry
