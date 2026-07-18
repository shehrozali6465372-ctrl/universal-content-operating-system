"""EpisodicMemory — store and recall specific experiences and events."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import MemoryEntry, MemoryType


class EpisodicMemory:
    """Store and recall specific experiences and events with temporal context."""

    def __init__(self) -> None:
        self._entries: List[MemoryEntry] = []
        self._max_entries = 1000

    def store_event(self, event: str, context: Optional[Dict[str, Any]] = None,
                    importance: float = 0.5) -> MemoryEntry:
        metadata = {"event_type": "episode", "context": context or {}}
        entry = MemoryEntry(
            content=event, memory_type=MemoryType.EPISODIC,
            importance=importance, metadata=metadata,
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def recall_recent(self, limit: int = 5) -> List[MemoryEntry]:
        return sorted(self._entries, key=lambda e: e.created_at, reverse=True)[:limit]

    def recall_by_time(self, start: float, end: float) -> List[MemoryEntry]:
        return [e for e in self._entries if start <= e.created_at <= end]

    def recall_important(self, min_importance: float = 0.7, limit: int = 5) -> List[MemoryEntry]:
        important = [e for e in self._entries if e.importance >= min_importance]
        return sorted(important, key=lambda e: e.importance, reverse=True)[:limit]

    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        query_words = set(query.lower().split())
        scored = []
        for e in self._entries:
            content_words = set(e.content.lower().split())
            overlap = query_words & content_words
            score = len(overlap) / max(len(query_words), 1) if query_words else 0.0
            if score > 0:
                scored.append((e, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:limit]]

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
