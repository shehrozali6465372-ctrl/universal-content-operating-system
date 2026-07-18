"""LongTermMemory — persistent long-term knowledge storage with decay."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .models import MemoryEntry, MemoryType


class LongTermMemory:
    """Persistent long-term knowledge storage with importance decay."""

    def __init__(self, max_entries: int = 5000, decay_rate: float = 0.01) -> None:
        self.max_entries = max_entries
        self.decay_rate = decay_rate
        self._entries: List[MemoryEntry] = []

    def store(self, content: str, importance: float = 0.5,
              tags: Optional[List[str]] = None,
              metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
        entry = MemoryEntry(
            content=content, memory_type=MemoryType.LONG_TERM,
            importance=importance, tags=tags or [], metadata=metadata or {},
        )
        self._entries.append(entry)
        self._evict_if_needed()
        return entry

    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        for e in self._entries:
            if e.entry_id == entry_id:
                e.touch()
                return e
        return None

    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        query_words = set(query.lower().split())
        scored = []
        for e in self._entries:
            content_words = set(e.content.lower().split())
            overlap = query_words & content_words
            score = len(overlap) / max(len(query_words), 1) if query_words else 0.0
            score += e.importance * 0.2
            if score > 0:
                scored.append((e, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:limit]]

    def get_important(self, min_importance: float = 0.7, limit: int = 10) -> List[MemoryEntry]:
        important = [e for e in self._entries if e.importance >= min_importance]
        return sorted(important, key=lambda e: e.importance, reverse=True)[:limit]

    def apply_decay(self) -> int:
        """Apply time-based decay to all entries. Returns count of entries removed."""
        now = time.time()
        for e in self._entries:
            age_days = (now - e.created_at) / 86400
            e.importance *= (1 - self.decay_rate * age_days)
            e.importance = max(0.01, e.importance)
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.importance > 0.05]
        self._evict_if_needed()
        return before - len(self._entries)

    def _evict_if_needed(self) -> None:
        if len(self._entries) > self.max_entries:
            self._entries.sort(key=lambda e: e.importance)
            self._entries = self._entries[-self.max_entries:]

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
