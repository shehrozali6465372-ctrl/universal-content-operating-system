"""Optimization Memory — Store successful optimization patterns."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

_OM_COUNTER = itertools.count(1)


class OptimizationMemoryEntry:
    """A stored optimization pattern."""

    __slots__ = ("entry_id", "pattern_type", "description", "context",
                 "success_rate", "usage_count", "tags", "created_at")

    def __init__(self, pattern_type: str = "", description: str = "") -> None:
        self.entry_id: str = f"ome_{next(_OM_COUNTER)}"
        self.pattern_type = pattern_type
        self.description = description
        self.context: Dict[str, Any] = {}
        self.success_rate: float = 0.5
        self.usage_count: int = 0
        self.tags: List[str] = []
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "success_rate": round(self.success_rate, 3),
            "usage_count": self.usage_count,
            "tags": self.tags,
        }


class OptimizationMemory:
    """Store and retrieve optimization patterns and learnings."""

    def __init__(self, max_entries: int = 5000) -> None:
        self._max_entries = max_entries
        self._entries: List[OptimizationMemoryEntry] = []

    def store(self, pattern_type: str, description: str,
              context: Optional[Dict[str, Any]] = None,
              success_rate: float = 0.5,
              tags: Optional[List[str]] = None) -> OptimizationMemoryEntry:
        entry = OptimizationMemoryEntry(pattern_type, description)
        if context:
            entry.context = dict(context)
        entry.success_rate = success_rate
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def search(self, pattern_type: str = "", tag: str = "",
               min_success_rate: float = 0.0,
               limit: int = 50) -> List[OptimizationMemoryEntry]:
        results = self._entries
        if pattern_type:
            results = [e for e in results if e.pattern_type == pattern_type]
        if tag:
            results = [e for e in results if tag in e.tags]
        if min_success_rate > 0:
            results = [e for e in results if e.success_rate >= min_success_rate]
        return results[-limit:]

    def get_top_patterns(self, count: int = 5) -> List[OptimizationMemoryEntry]:
        sorted_entries = sorted(self._entries, key=lambda e: e.success_rate, reverse=True)
        return sorted_entries[:count]

    def get_by_id(self, entry_id: str) -> OptimizationMemoryEntry | None:
        for e in self._entries:
            if e.entry_id == entry_id:
                return e
        return None

    def get_stats(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for e in self._entries:
            by_type[e.pattern_type] = by_type.get(e.pattern_type, 0) + 1
        avg_success = 0.0
        if self._entries:
            avg_success = sum(e.success_rate for e in self._entries) / len(self._entries)
        return {
            "total": len(self._entries),
            "by_type": by_type,
            "avg_success_rate": round(avg_success, 3),
        }

    @property
    def entry_count(self) -> int:
        return len(self._entries)
