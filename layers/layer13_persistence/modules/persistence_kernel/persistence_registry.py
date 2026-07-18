"""persistence_registry.py — Persistence component registry."""
from __future__ import annotations
from typing import Any, Dict


class PersistenceRegistry:
    """Registry for persistence components."""

    def __init__(self) -> None:
        self._components: Dict[str, Any] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, component: Any,
                 component_type: str = "unknown") -> None:
        self._components[name] = component
        self._metadata[name] = {"type": component_type}

    def unregister(self, name: str) -> bool:
        if name in self._components:
            del self._components[name]
            self._metadata.pop(name, None)
            return True
        return False

    def get(self, name: str) -> Any:
        return self._components.get(name)

    def has(self, name: str) -> bool:
        return name in self._components

    def list_all(self) -> Dict[str, Any]:
        return dict(self._components)

    def list_by_type(self, component_type: str) -> Dict[str, Any]:
        return {k: v for k, (v, m) in zip(self._components.items(),
                [self._metadata.get(k, {}) for k in self._components])
                if self._metadata.get(k, {}).get("type") == component_type}

    def count(self) -> int:
        return len(self._components)

    def stats(self) -> Dict[str, Any]:
        types = {}
        for m in self._metadata.values():
            t = m.get("type", "unknown")
            types[t] = types.get(t, 0) + 1
        return {"total": len(self._components), "by_type": types}
