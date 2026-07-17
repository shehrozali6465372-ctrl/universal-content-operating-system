"""Meta Memory — High-level system memory."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_MM_COUNTER = itertools.count(1)


class MemoryEntry:
    """A high-level memory entry."""

    __slots__ = ("entry_id", "category", "content", "importance",
                 "tags", "created_at", "access_count")

    def __init__(self, category: str = "", content: str = "") -> None:
        self.entry_id: str = f"mem_{next(_MM_COUNTER)}"
        self.category = category
        self.content = content
        self.importance: float = 0.5
        self.tags: List[str] = []
        self.created_at: float = time.time()
        self.access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id, "category": self.category,
            "importance": round(self.importance, 3), "access_count": self.access_count,
        }


class MetaMemory:
    """Store and retrieve high-level system knowledge."""

    CATEGORIES = ("goal", "strategy", "failure", "success", "lesson",
                  "campaign", "platform", "decision")

    def __init__(self, max_entries: int = 5000) -> None:
        self._max_entries = max_entries
        self._entries: List[MemoryEntry] = []

    def store(self, category: str, content: str, importance: float = 0.5,
              tags: Optional[List[str]] = None) -> MemoryEntry:
        entry = MemoryEntry(category, content)
        entry.importance = importance
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def search(self, category: str = "", tag: str = "",
               min_importance: float = 0.0, limit: int = 50) -> List[MemoryEntry]:
        results = self._entries
        if category:
            results = [e for e in results if e.category == category]
        if tag:
            results = [e for e in results if tag in e.tags]
        if min_importance > 0:
            results = [e for e in results if e.importance >= min_importance]
        return results[-limit:]

    def get_recent(self, count: int = 10) -> List[MemoryEntry]:
        return self._entries[-count:]

    def get_stats(self) -> Dict[str, Any]:
        by_cat: Dict[str, int] = {}
        for e in self._entries:
            by_cat[e.category] = by_cat.get(e.category, 0) + 1
        return {"total": len(self._entries), "by_category": by_cat}
