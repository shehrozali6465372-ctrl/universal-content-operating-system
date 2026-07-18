"""namespace_manager.py — Namespace management for vectors."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class Namespace:
    """A namespace for organizing vectors."""
    __slots__ = ("name", "description", "dimensions", "metadata", "record_count")

    def __init__(self, name: str, dimensions: int = 1536) -> None:
        self.name = name
        self.description: str = ""
        self.dimensions = dimensions
        self.metadata: Dict[str, Any] = {}
        self.record_count: int = 0


class NamespaceManager:
    """Manages vector namespaces."""

    def __init__(self) -> None:
        self._namespaces: Dict[str, Namespace] = {}

    def create(self, name: str, dimensions: int = 1536) -> Namespace:
        ns = Namespace(name, dimensions)
        self._namespaces[name] = ns
        return ns

    def delete(self, name: str) -> bool:
        return self._namespaces.pop(name, None) is not None

    def get(self, name: str) -> Optional[Namespace]:
        return self._namespaces.get(name)

    def list_all(self) -> List[Namespace]:
        return list(self._namespaces.values())

    def count(self) -> int:
        return len(self._namespaces)
