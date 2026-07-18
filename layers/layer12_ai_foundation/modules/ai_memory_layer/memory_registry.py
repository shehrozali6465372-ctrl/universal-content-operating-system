"""MemoryRegistry — register and manage memory store instances."""
from __future__ import annotations

from typing import Any, Dict, Optional


class MemoryRegistry:
    """Registry of memory store instances."""

    def __init__(self) -> None:
        self._stores: Dict[str, Any] = {}

    def register(self, name: str, store: Any) -> None:
        self._stores[name] = store

    def unregister(self, name: str) -> bool:
        return self._stores.pop(name, None) is not None

    def get(self, name: str) -> Optional[Any]:
        return self._stores.get(name)

    def list_stores(self) -> list:
        return list(self._stores.keys())

    def count(self) -> int:
        return len(self._stores)

    def to_dict(self) -> Dict[str, Any]:
        return {name: type(store).__name__ for name, store in self._stores.items()}
