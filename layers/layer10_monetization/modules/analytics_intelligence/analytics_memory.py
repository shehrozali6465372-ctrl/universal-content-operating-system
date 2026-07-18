"""AnalyticsMemory — Store and retrieve historical analytics data."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_AM_COUNTER = itertools.count(1)


class AnalyticsMemoryEntry:
    """A stored analytics memory entry."""

    __slots__ = ("entry_id", "platform", "post_id", "metrics",
                 "content_type", "tags", "score", "created_at",
                 "access_count", "metadata")

    def __init__(self, platform: str = "", post_id: str = "") -> None:
        self.entry_id: str = f"amem_{next(_AM_COUNTER)}"
        self.platform = platform
        self.post_id = post_id
        self.metrics: Dict[str, Any] = {}
        self.content_type: str = "post"
        self.tags: List[str] = []
        self.score: float = 0.0
        self.created_at: float = time.time()
        self.access_count: int = 0
        self.metadata: Dict[str, Any] = {}


class AnalyticsMemory:
    """Store and retrieve historical analytics with comparison."""

    def __init__(self, max_entries: int = 10000) -> None:
        self._max_entries = max_entries
        self._entries: List[AnalyticsMemoryEntry] = []
        self._entries_index: Dict[str, AnalyticsMemoryEntry] = {}

    def store(self, platform: str, post_id: str, metrics: Dict[str, Any],
              content_type: str = "post", tags: Optional[List[str]] = None,
              score: float = 0.0) -> AnalyticsMemoryEntry:
        entry = AnalyticsMemoryEntry(platform, post_id)
        entry.metrics = dict(metrics)
        entry.content_type = content_type
        entry.score = score
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        self._entries_index[entry.entry_id] = entry
        if len(self._entries) > self._max_entries:
            oldest = self._entries[:len(self._entries) - self._max_entries]
            for e in oldest:
                self._entries_index.pop(e.entry_id, None)
            self._entries = self._entries[-self._max_entries:]
        return entry

    def search(self, platform: str = "", content_type: str = "",
               tag: str = "", min_score: float = 0.0,
               limit: int = 50) -> List[AnalyticsMemoryEntry]:
        results = self._entries
        if platform:
            results = [e for e in results if e.platform == platform]
        if content_type:
            results = [e for e in results if e.content_type == content_type]
        if tag:
            results = [e for e in results if tag in e.tags]
        if min_score > 0:
            results = [e for e in results if e.score >= min_score]
        return results[-limit:]

    def get_recent(self, count: int = 10, platform: str = "") -> List[AnalyticsMemoryEntry]:
        entries = self._entries
        if platform:
            entries = [e for e in entries if e.platform == platform]
        return entries[-count:]

    def get_best_performing(self, platform: str = "", count: int = 5) -> List[AnalyticsMemoryEntry]:
        entries = self._entries
        if platform:
            entries = [e for e in entries if e.platform == platform]
        return sorted(entries, key=lambda e: e.score, reverse=True)[:count]

    def get_by_platform(self, platform: str) -> List[AnalyticsMemoryEntry]:
        return [e for e in self._entries if e.platform == platform]

    def compare_periods(self, days_1_start: float, days_1_end: float,
                        days_2_start: float, days_2_end: float) -> Dict[str, Any]:
        period1 = [e for e in self._entries if days_1_start <= e.created_at <= days_1_end]
        period2 = [e for e in self._entries if days_2_start <= e.created_at <= days_2_end]
        avg1 = sum(e.score for e in period1) / max(1, len(period1))
        avg2 = sum(e.score for e in period2) / max(1, len(period2))
        return {"period1_count": len(period1), "period2_count": len(period2),
                "period1_avg_score": round(avg1, 3), "period2_avg_score": round(avg2, 3),
                "change": round(avg2 - avg1, 3)}

    def get_stats(self) -> Dict[str, Any]:
        platforms: Dict[str, int] = {}
        for e in self._entries:
            platforms[e.platform] = platforms.get(e.platform, 0) + 1
        return {"total": len(self._entries), "by_platform": platforms}
