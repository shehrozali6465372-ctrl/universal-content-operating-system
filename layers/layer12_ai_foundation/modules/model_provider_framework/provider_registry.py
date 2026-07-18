"""provider_registry.py — Registry for all AI model providers."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import BaseProvider


class ProviderRegistry:
    """Registry for managing all AI model providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseProvider] = {}
        self._aliases: Dict[str, str] = {}

    def register(self, provider: BaseProvider) -> bool:
        name = provider.name.lower()
        self._providers[name] = provider
        return True

    def unregister(self, name: str) -> bool:
        key = name.lower()
        if key in self._providers:
            del self._providers[key]
            return True
        return False

    def get(self, name: str) -> Optional[BaseProvider]:
        key = name.lower()
        if key in self._providers:
            return self._providers[key]
        if key in self._aliases:
            return self._providers.get(self._aliases[key])
        return None

    def get_all(self) -> List[BaseProvider]:
        return list(self._providers.values())

    def get_available(self) -> List[BaseProvider]:
        return [p for p in self._providers.values() if p.is_available()]

    def has_provider(self, name: str) -> bool:
        return name.lower() in self._providers

    def add_alias(self, alias: str, target: str) -> None:
        self._aliases[alias.lower()] = target.lower()

    def count(self) -> int:
        return len(self._providers)

    def list_names(self) -> List[str]:
        return list(self._providers.keys())

    def clear(self) -> None:
        self._providers.clear()
        self._aliases.clear()

    def get_by_capability(self, capability: str) -> List[BaseProvider]:
        return [p for p in self._providers.values()
                if capability in getattr(p, "capabilities", [])]

    def to_dict(self) -> Dict[str, Any]:
        return {"providers": list(self._providers.keys()),
                "aliases": dict(self._aliases), "count": self.count()}
