"""Analytics Memory — Store historical metrics for comparison and trends."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.analytics_hook.analytics_event import AnalyticsEvent


class HistoricalRecord:
    """A stored analytics snapshot."""

    __slots__ = ("post_id", "platform", "timestamp", "metrics", "snapshot_id")

    def __init__(self, post_id: str, platform: str, metrics: Dict[str, Any]) -> None:
        self.snapshot_id = f"snap_{post_id}_{int(time.time())}"
        self.post_id = post_id
        self.platform = platform
        self.timestamp: float = time.time()
        self.metrics = dict(metrics)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "post_id": self.post_id,
            "platform": self.platform,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
        }


class AnalyticsMemory:
    """Store and retrieve historical analytics data."""

    def __init__(self, max_records: int = 10000) -> None:
        self._max_records = max_records
        self._records: List[HistoricalRecord] = []
        self._index: Dict[str, List[int]] = {}

    def store(self, event: AnalyticsEvent) -> HistoricalRecord:
        rec = HistoricalRecord(event.post_id, event.platform, event.metrics)
        self._records.append(rec)
        idx = len(self._records) - 1
        self._index.setdefault(event.post_id, []).append(idx)

        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
            self._index.clear()
        return rec

    def get_history(self, post_id: str) -> List[HistoricalRecord]:
        indices = self._index.get(post_id, [])
        return [self._records[i] for i in indices if i < len(self._records)]

    def get_latest(self, post_id: str) -> Optional[HistoricalRecord]:
        history = self.get_history(post_id)
        return history[-1] if history else None

    def get_platform_history(self, platform: str) -> List[HistoricalRecord]:
        return [r for r in self._records if r.platform == platform]

    def compare(self, post_id: str) -> Optional[Dict[str, Any]]:
        history = self.get_history(post_id)
        if len(history) < 2:
            return None
        first = history[0].metrics
        last = history[-1].metrics
        changes: Dict[str, Any] = {}
        for key in set(list(first.keys()) + list(last.keys())):
            v1 = first.get(key, 0)
            v2 = last.get(key, 0)
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                changes[key] = {"first": v1, "latest": v2, "change": v2 - v1}
        return changes

    @property
    def record_count(self) -> int:
        return len(self._records)
