"""provider_loader.py — Dynamic provider loading."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_factory import ProviderFactory
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_registry import ProviderRegistry


class ProviderLoader:
    """Loads and initializes providers from configuration."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry
        self._loaded: List[str] = []

    def load_all(self, configs: Dict[str, Dict[str, Any]]) -> int:
        count = 0
        for name, config in configs.items():
            if self.load(name, config):
                count += 1
        return count

    def load(self, name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        provider = ProviderFactory.create(name, config)
        if provider:
            self._registry.register(provider)
            self._loaded.append(name)
            return True
        return False

    def get_loaded(self) -> List[str]:
        return list(self._loaded)

    def unload(self, name: str) -> bool:
        self._registry.unregister(name)
        if name in self._loaded:
            self._loaded.remove(name)
            return True
        return False
