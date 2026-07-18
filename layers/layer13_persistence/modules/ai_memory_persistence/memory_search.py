"""memory_search.py — Universal memory search across all stores."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore


class MemorySearch:
    """Searches across multiple memory stores."""

    def __init__(self) -> None:
        self._stores: Dict[str, BaseMemoryStore] = {}

    def register_store(self, name: str, store: BaseMemoryStore) -> None:
        self._stores[name] = store

    def search(self, query: str, store_name: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        stores = [self._stores[store_name]] if store_name else list(self._stores.values())
        for store in stores:
            for entry in store.search(query, limit):
                results.append({"store": store._memory_type, "entry": entry.to_dict(),
                                "score": entry.access_count})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    def search_all(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self.search(query, limit=limit)

    def count_all(self) -> Dict[str, int]:
        return {name: store.count() for name, store in self._stores.items()}

    def stats(self) -> Dict[str, Any]:
        return {"stores": len(self._stores),
                "counts": {n: s.count() for n, s in self._stores.items()}}
