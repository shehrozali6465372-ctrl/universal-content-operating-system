"""research_memory_store.py — Research memory persistence."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class ResearchMemoryStore(BaseMemoryStore):
    """Stores research findings and cached results."""

    def __init__(self, max_entries: int = 5000) -> None:
        super().__init__("research", max_entries)
        self._sources: Dict[str, Dict[str, Any]] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "research")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def cache_result(self, query: str, result: Any, ttl: float = 3600.0) -> None:
        import time
        self._cache[query] = {"result": result, "created_at": time.time(), "ttl": ttl}

    def get_cached(self, query: str) -> Optional[Any]:
        import time
        entry = self._cache.get(query)
        if entry and (time.time() - entry["created_at"]) < entry["ttl"]:
            return entry["result"]
        return None

    def register_source(self, name: str, trust_score: float = 0.5) -> None:
        self._sources[name] = {"trust_score": trust_score}

    def get_sources(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._sources)

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["sources"] = len(self._sources)
        base["cached"] = len(self._cache)
        return base
