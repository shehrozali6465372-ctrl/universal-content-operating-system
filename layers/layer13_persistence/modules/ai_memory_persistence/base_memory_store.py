"""base_memory_store.py — Base class for all memory stores."""
from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MemoryEntry:
    """Single memory entry."""
    __slots__ = ("entry_id", "key", "value", "memory_type", "metadata",
                 "created_at", "updated_at", "access_count", "confidence", "version")
    _counter = 0

    def __init__(self, key: str, value: Any, memory_type: str = "general") -> None:
        MemoryEntry._counter += 1
        self.entry_id: int = MemoryEntry._counter
        self.key = key
        self.value = value
        self.memory_type = memory_type
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.access_count: int = 0
        self.confidence: float = 1.0
        self.version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.entry_id, "key": self.key, "type": self.memory_type,
                "confidence": self.confidence, "version": self.version,
                "access_count": self.access_count}


class BaseMemoryStore(ABC):
    """Abstract base for all memory stores."""

    def __init__(self, memory_type: str, max_entries: int = 10000) -> None:
        self._memory_type = memory_type
        self._max_entries = max_entries
        self._store: Dict[str, MemoryEntry] = {}
        self._version_history: Dict[str, List[Any]] = {}

    @abstractmethod
    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        ...

    @abstractmethod
    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        ...

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        return key in self._store

    def count(self) -> int:
        return len(self._store)

    def list_keys(self) -> List[str]:
        return list(self._store.keys())

    def get_all(self) -> List[MemoryEntry]:
        return list(self._store.values())

    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        results = [e for e in self._store.values() if query.lower() in str(e.value).lower()]
        results.sort(key=lambda e: e.access_count, reverse=True)
        return results[:limit]

    def cleanup(self) -> int:
        if len(self._store) <= self._max_entries:
            return 0
        sorted_entries = sorted(self._store.values(), key=lambda e: e.access_count)
        to_remove = len(self._store) - self._max_entries
        for entry in sorted_entries[:to_remove]:
            self._store.pop(entry.key, None)
        return to_remove

    def stats(self) -> Dict[str, Any]:
        return {"type": self._memory_type, "entries": len(self._store),
                "max": self._max_entries}
