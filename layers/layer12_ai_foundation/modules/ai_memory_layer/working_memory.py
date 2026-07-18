"""WorkingMemory — short-term active memory for current context."""
from __future__ import annotations

from typing import List, Optional

from .models import MemoryEntry, MemoryType


class WorkingMemory:
    """Short-term active memory for current context and tasks."""

    def __init__(self, max_items: int = 50) -> None:
        self.max_items = max_items
        self._items: List[MemoryEntry] = []
        self._focus: Optional[str] = None

    def add(self, content: str, importance: float = 0.5,
            tags: Optional[List[str]] = None) -> MemoryEntry:
        entry = MemoryEntry(
            content=content, memory_type=MemoryType.WORKING,
            importance=importance, tags=tags or [],
        )
        self._items.append(entry)
        if len(self._items) > self.max_items:
            self._items.sort(key=lambda e: e.importance)
            self._items.pop(0)
        return entry

    def set_focus(self, topic: str) -> None:
        self._focus = topic

    def get_focus(self) -> Optional[str]:
        return self._focus

    def get_items(self, limit: int = 10) -> List[MemoryEntry]:
        return sorted(self._items, key=lambda e: e.importance, reverse=True)[:limit]

    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        query_words = set(query.lower().split())
        scored = []
        for e in self._items:
            content_words = set(e.content.lower().split())
            overlap = query_words & content_words
            score = len(overlap) / max(len(query_words), 1) if query_words else 0.0
            if score > 0:
                scored.append((e, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:limit]]

    def clear(self) -> None:
        self._items.clear()
        self._focus = None

    def count(self) -> int:
        return len(self._items)
