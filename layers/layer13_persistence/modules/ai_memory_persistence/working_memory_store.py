"""working_memory_store.py — Working (short-term) memory persistence."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class WorkingMemoryStore(BaseMemoryStore):
    """Stores short-term working memory with automatic expiry."""

    def __init__(self, max_entries: int = 500, default_ttl: float = 600.0) -> None:
        super().__init__("working", max_entries)
        self._default_ttl = default_ttl
        self._timestamps: Dict[str, float] = {}

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        import time
        entry = MemoryEntry(key, value, "working")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        self._timestamps[key] = time.time()
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        import time
        entry = self._store.get(key)
        if entry:
            ts = self._timestamps.get(key, 0)
            if (time.time() - ts) > self._default_ttl:
                self._store.pop(key, None)
                self._timestamps.pop(key, None)
                return None
            entry.access_count += 1
        return entry

    def cleanup_expired(self) -> int:
        import time
        now = time.time()
        expired = [k for k, ts in self._timestamps.items() if (now - ts) > self._default_ttl]
        for k in expired:
            self._store.pop(k, None)
            self._timestamps.pop(k, None)
        return len(expired)

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["with_ttl"] = len(self._timestamps)
        return base
