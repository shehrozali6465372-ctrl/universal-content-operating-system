"""GlobalMemory — System-wide memory: short-term, long-term, semantic, episodic, business."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_GM_COUNTER = itertools.count(1)

MEMORY_TYPES = ("short_term", "long_term", "semantic", "episodic", "business", "system")


class MemoryEntry:
    """A global memory entry."""

    __slots__ = ("entry_id", "memory_type", "key", "data",
                 "confidence", "tags", "importance", "created_at",
                 "last_accessed", "access_count")

    def __init__(self, memory_type: str = "", key: str = "",
                 data: Any = None) -> None:
        self.entry_id: str = f"gmem_{next(_GM_COUNTER)}"
        self.memory_type = memory_type if memory_type in MEMORY_TYPES else "short_term"
        self.key = key
        self.data = data
        self.confidence: float = 0.5
        self.tags: List[str] = []
        self.importance: int = 1
        self.created_at: float = time.time()
        self.last_accessed: float = time.time()
        self.access_count: int = 0


class GlobalMemory:
    """System-wide memory center for all learned knowledge."""

    def __init__(self, max_entries: int = 50000) -> None:
        self._max_entries = max_entries
        self._entries: List[MemoryEntry] = []
        self._index: Dict[str, MemoryEntry] = {}

    def store(self, memory_type: str, key: str, data: Any,
              confidence: float = 0.5, tags: Optional[List[str]] = None,
              importance: int = 1) -> MemoryEntry:
        idx_key = f"{memory_type}:{key}"
        if idx_key in self._index:
            entry = self._index[idx_key]
            entry.data = data
            entry.confidence = confidence
            entry.last_accessed = time.time()
            return entry
        entry = MemoryEntry(memory_type, key, data)
        entry.confidence = confidence
        entry.importance = importance
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        self._index[idx_key] = entry
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def retrieve(self, memory_type: str, key: str) -> Any:
        entry = self._index.get(f"{memory_type}:{key}")
        if entry:
            entry.access_count += 1
            entry.last_accessed = time.time()
            return entry.data
        return None

    def search(self, memory_type: str = "", query: str = "",
               tag: str = "", min_confidence: float = 0.0,
               limit: int = 50) -> List[MemoryEntry]:
        results = self._entries
        if memory_type:
            results = [e for e in results if e.memory_type == memory_type]
        if query:
            results = [e for e in results if query.lower() in e.key.lower()]
        if tag:
            results = [e for e in results if tag in e.tags]
        if min_confidence > 0:
            results = [e for e in results if e.confidence >= min_confidence]
        return results[-limit:]

    def delete(self, memory_type: str, key: str) -> bool:
        idx_key = f"{memory_type}:{key}"
        entry = self._index.pop(idx_key, None)
        if entry:
            self._entries.remove(entry)
            return True
        return False

    def get_by_type(self, memory_type: str) -> List[MemoryEntry]:
        return [e for e in self._entries if e.memory_type == memory_type]

    def get_most_accessed(self, count: int = 10) -> List[MemoryEntry]:
        return sorted(self._entries, key=lambda e: e.access_count, reverse=True)[:count]

    def get_most_important(self, count: int = 10) -> List[MemoryEntry]:
        return sorted(self._entries, key=lambda e: e.importance, reverse=True)[:count]

    def clear(self, memory_type: str = "") -> int:
        if memory_type:
            to_remove = [e for e in self._entries if e.memory_type == memory_type]
            for e in to_remove:
                self._index.pop(f"{e.memory_type}:{e.key}", None)
                self._entries.remove(e)
            return len(to_remove)
        count = len(self._entries)
        self._entries.clear()
        self._index.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for e in self._entries:
            types[e.memory_type] = types.get(e.memory_type, 0) + 1
        return {"total": len(self._entries), "by_type": types,
                "max_capacity": self._max_entries}
