"""SemanticMemory — store and retrieve knowledge facts and concepts."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import MemoryEntry, MemoryType


class SemanticMemory:
    """Store and retrieve knowledge facts, concepts, and relationships."""

    def __init__(self) -> None:
        self._entries: List[MemoryEntry] = []
        self._max_entries = 2000

    def store(self, content: str, tags: Optional[List[str]] = None,
              importance: float = 0.5, metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
        entry = MemoryEntry(
            content=content, memory_type=MemoryType.SEMANTIC,
            tags=tags or [], importance=importance, metadata=metadata or {},
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.sort(key=lambda e: e.importance)
            self._entries.pop(0)
        return entry

    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        for e in self._entries:
            if e.entry_id == entry_id:
                e.touch()
                return e
        return None

    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        query_lower = query.lower()
        scored = []
        for e in self._entries:
            score = 0.0
            content_lower = e.content.lower()
            # Simple keyword matching
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            overlap = query_words & content_words
            if query_words:
                score = len(overlap) / len(query_words)
            # Boost by importance
            score += e.importance * 0.3
            if score > 0:
                scored.append((e, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:limit]]

    def get_by_tag(self, tag: str) -> List[MemoryEntry]:
        return [e for e in self._entries if tag in e.tags]

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
