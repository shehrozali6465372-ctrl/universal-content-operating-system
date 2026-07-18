"""analytics_memory_store.py — Analytics memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class AnalyticsMemoryStore(BaseMemoryStore):
    """Stores analytics insights and metrics history."""

    def __init__(self, max_entries: int = 10000) -> None:
        super().__init__("analytics", max_entries)
        self._time_series: Dict[str, List[Dict[str, Any]]] = {}
        self._insights: List[Dict[str, Any]] = []

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "analytics")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def record_metric(self, metric_name: str, value: float,
                      metadata: Dict[str, Any] = None) -> None:
        import time
        if metric_name not in self._time_series:
            self._time_series[metric_name] = []
        self._time_series[metric_name].append({"value": value, "timestamp": time.time(),
                                                 "metadata": metadata or {}})

    def get_time_series(self, metric_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self._time_series.get(metric_name, [])[-limit:]

    def add_insight(self, insight: Dict[str, Any]) -> None:
        self._insights.append(insight)

    def get_insights(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._insights[-limit:]

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["metrics"] = len(self._time_series)
        base["insights"] = len(self._insights)
        return base
