"""FinancialMemory — Remember successful strategies and failed experiments."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_FM_COUNTER = itertools.count(1)


class FinancialMemoryEntry:
    """A stored financial memory entry."""

    __slots__ = ("entry_id", "category", "key", "data", "confidence",
                 "tags", "created_at", "access_count")

    def __init__(self, category: str = "", key: str = "") -> None:
        self.entry_id: str = f"fmem_{next(_FM_COUNTER)}"
        self.category = category
        self.key = key
        self.data: Dict[str, Any] = {}
        self.confidence: float = 0.5
        self.tags: List[str] = []
        self.created_at: float = time.time()
        self.access_count: int = 0


class FinancialMemory:
    """Store successful strategies, failed campaigns, seasonal trends, and revenue history."""

    def __init__(self, max_entries: int = 5000) -> None:
        self._max_entries = max_entries
        self._entries: List[FinancialMemoryEntry] = []

    def store(self, category: str, key: str, data: Dict[str, Any],
              confidence: float = 0.5, tags: Optional[List[str]] = None) -> FinancialMemoryEntry:
        entry = FinancialMemoryEntry(category, key)
        entry.data = dict(data)
        entry.confidence = confidence
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def search(self, category: str = "", key: str = "",
               tag: str = "", min_confidence: float = 0.0,
               limit: int = 50) -> List[FinancialMemoryEntry]:
        results = self._entries
        if category:
            results = [e for e in results if e.category == category]
        if key:
            results = [e for e in results if key.lower() in e.key.lower()]
        if tag:
            results = [e for e in results if tag in e.tags]
        if min_confidence > 0:
            results = [e for e in results if e.confidence >= min_confidence]
        return results[-limit:]

    def get_latest(self, category: str = "", count: int = 10) -> List[FinancialMemoryEntry]:
        entries = self._entries
        if category:
            entries = [e for e in entries if e.category == category]
        return entries[-count:]

    def get_successful(self, min_confidence: float = 0.7) -> List[FinancialMemoryEntry]:
        return [e for e in self._entries if e.confidence >= min_confidence]

    def get_failed(self) -> List[FinancialMemoryEntry]:
        return [e for e in self._entries if e.confidence < 0.3]

    def get_by_category(self, category: str) -> List[FinancialMemoryEntry]:
        return [e for e in self._entries if e.category == category]

    def get_stats(self) -> Dict[str, Any]:
        categories: Dict[str, int] = {}
        for e in self._entries:
            categories[e.category] = categories.get(e.category, 0) + 1
        return {"total": len(self._entries), "by_category": categories}
