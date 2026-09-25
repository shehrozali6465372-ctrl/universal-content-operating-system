"""GlobalMemory — bounded system memory with index consistency."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_GM_COUNTER = itertools.count(1)
MEMORY_TYPES = ("short_term", "long_term", "semantic", "episodic", "business", "system")


class MemoryEntry:
    """A global memory entry."""

    def __init__(self, memory_type: str, key: str, data: Any) -> None:
        self.entry_id = f"gmem_{next(_GM_COUNTER)}"
        self.memory_type = memory_type if memory_type in MEMORY_TYPES else "short_term"
        self.key = key
        self.data = data
        self.confidence = 0.5
        self.tags: List[str] = []
        self.importance = 1
        self.created_at = time.time()
        self.last_accessed = self.created_at
        self.access_count = 0


class GlobalMemory:
    """System-wide memory center for all learned knowledge."""

    def __init__(self, max_entries: int = 50000) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self._max_entries = max_entries
        self._entries: List[MemoryEntry] = []
        self._index: Dict[str, MemoryEntry] = {}

    def store(self, memory_type: str, key: str, data: Any,
              confidence: float = 0.5, tags: Optional[List[str]] = None,
              importance: int = 1) -> MemoryEntry:
        if not key:
            raise ValueError("key is required")
        idx_key = f"{memory_type}:{key}"
        existing = self._index.get(idx_key)
        if existing is not None:
            existing.data = data
            existing.confidence = max(0.0, min(1.0, confidence))
            existing.importance = importance
            existing.tags = list(tags or [])
            existing.last_accessed = time.time()
            return existing
        entry = MemoryEntry(memory_type, key, data)
        entry.confidence = max(0.0, min(1.0, confidence))
        entry.importance = importance
        entry.tags = list(tags or [])
        self._entries.append(entry)
        self._index[idx_key] = entry
        while len(self._entries) > self._max_entries:
            evicted = self._entries.pop(0)
            self._index.pop(f"{evicted.memory_type}:{evicted.key}", None)
        return entry

    def retrieve(self, memory_type: str, key: str) -> Any:
        entry = self._index.get(f"{memory_type}:{key}")
        if entry is None:
            return None
        entry.access_count += 1
        entry.last_accessed = time.time()
        return entry.data

    def search(self, memory_type: str = "", query: str = "",
               tag: str = "", min_confidence: float = 0.0,
               limit: int = 50) -> List[MemoryEntry]:
        if limit <= 0:
            return []
        results = self._entries
        if memory_type:
            results = [e for e in results if e.memory_type == memory_type]
        if query:
            needle = query.lower()
            results = [e for e in results if needle in e.key.lower()]
        if tag:
            results = [e for e in results if tag in e.tags]
        if min_confidence > 0:
            results = [e for e in results if e.confidence >= min_confidence]
        return list(results[-limit:])

    def delete(self, memory_type: str, key: str) -> bool:
        entry = self._index.pop(f"{memory_type}:{key}", None)
        if entry is None:
            return False
        self._entries.remove(entry)
        return True

    def get_by_type(self, memory_type: str) -> List[MemoryEntry]:
        return [entry for entry in self._entries if entry.memory_type == memory_type]

    def get_most_accessed(self, count: int = 10) -> List[MemoryEntry]:
        return sorted(self._entries, key=lambda entry: entry.access_count, reverse=True)[:count]

    def get_most_important(self, count: int = 10) -> List[MemoryEntry]:
        return sorted(self._entries, key=lambda entry: entry.importance, reverse=True)[:count]

    def clear(self, memory_type: str = "") -> int:
        if memory_type:
            to_remove = [entry for entry in self._entries if entry.memory_type == memory_type]
            for entry in to_remove:
                self._index.pop(f"{entry.memory_type}:{entry.key}", None)
            self._entries = [entry for entry in self._entries if entry.memory_type != memory_type]
            return len(to_remove)
        count = len(self._entries)
        self._entries.clear()
        self._index.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for entry in self._entries:
            types[entry.memory_type] = types.get(entry.memory_type, 0) + 1
        return {"total": len(self._entries), "by_type": types, "max_capacity": self._max_entries}
