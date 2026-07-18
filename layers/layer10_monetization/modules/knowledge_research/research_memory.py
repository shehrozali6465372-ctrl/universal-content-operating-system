"""ResearchMemory — Store research results and cached knowledge."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_RMEM_COUNTER = itertools.count(1)


class ResearchMemoryEntry:
    """A stored research memory."""

    __slots__ = ("entry_id", "query", "results", "source",
                 "confidence", "tags", "created_at", "access_count")

    def __init__(self, query: str = "") -> None:
        self.entry_id: str = f"rmem_{next(_RMEM_COUNTER)}"
        self.query = query
        self.results: Dict[str, Any] = {}
        self.source: str = ""
        self.confidence: float = 0.5
        self.tags: List[str] = []
        self.created_at: float = time.time()
        self.access_count: int = 0


class ResearchMemory:
    """Store previous research, cached results, and best sources."""

    def __init__(self, max_entries: int = 5000) -> None:
        self._max_entries = max_entries
        self._entries: List[ResearchMemoryEntry] = []

    def store(self, query: str, results: Dict[str, Any], source: str = "",
              confidence: float = 0.5, tags: Optional[List[str]] = None) -> ResearchMemoryEntry:
        entry = ResearchMemoryEntry(query)
        entry.results = dict(results)
        entry.source = source
        entry.confidence = confidence
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def search(self, query: str = "", tag: str = "",
               min_confidence: float = 0.0, limit: int = 50) -> List[ResearchMemoryEntry]:
        results = self._entries
        if query:
            results = [e for e in results if query.lower() in e.query.lower()]
        if tag:
            results = [e for e in results if tag in e.tags]
        if min_confidence > 0:
            results = [e for e in results if e.confidence >= min_confidence]
        return results[-limit:]

    def get_cached(self, query: str) -> Optional[ResearchMemoryEntry]:
        for e in reversed(self._entries):
            if e.query.lower() == query.lower():
                e.access_count += 1
                return e
        return None

    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._entries),
                "avg_confidence": round(sum(e.confidence for e in self._entries) / max(1, len(self._entries)), 3)}
