"""memory_router.py — Routes memory operations to correct store."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore


class MemoryRouter:
    """Routes memory operations to the appropriate store."""

    def __init__(self) -> None:
        self._stores: Dict[str, BaseMemoryStore] = {}
        self._routing: Dict[str, str] = {}

    def register_store(self, name: str, store: BaseMemoryStore) -> None:
        self._stores[name] = store

    def route(self, memory_type: str, store_name: str) -> None:
        self._routing[memory_type] = store_name

    def get_store(self, memory_type: str) -> Optional[BaseMemoryStore]:
        store_name = self._routing.get(memory_type, memory_type)
        return self._stores.get(store_name)

    def store(self, memory_type: str, key: str, value: Any) -> bool:
        store = self.get_store(memory_type)
        if store:
            store.store(key, value)
            return True
        return False

    def retrieve(self, memory_type: str, key: str) -> Optional[Any]:
        store = self.get_store(memory_type)
        if store:
            entry = store.retrieve(key)
            return entry.value if entry else None
        return None

    def list_stores(self) -> Dict[str, BaseMemoryStore]:
        return dict(self._stores)

    def stats(self) -> Dict[str, Any]:
        return {"stores": len(self._stores), "routes": len(self._routing)}
