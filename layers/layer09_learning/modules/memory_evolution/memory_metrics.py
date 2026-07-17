"""Memory Metrics — Track memory evolution performance metrics."""
from __future__ import annotations
from typing import Any, Dict, List


class MemoryEvolutionMetrics:
    """Track metrics across memory evolution operations."""

    def __init__(self) -> None:
        self._total_cleanups: int = 0
        self._total_merges: int = 0
        self._total_optimizations: int = 0
        self._total_searches: int = 0
        self._total_archives: int = 0
        self._total_restores: int = 0
        self._entries_cleaned: List[int] = []
        self._entries_merged: List[int] = []
        self._search_latencies: List[float] = []

    def record_cleanup(self, entries_removed: int = 0) -> None:
        self._total_cleanups += 1
        self._entries_cleaned.append(entries_removed)

    def record_merge(self, entries_merged: int = 0) -> None:
        self._total_merges += 1
        self._entries_merged.append(entries_merged)

    def record_optimization(self) -> None:
        self._total_optimizations += 1

    def record_search(self, latency_ms: float = 0.0, results: int = 0) -> None:
        self._total_searches += 1
        self._search_latencies.append(latency_ms)

    def record_archive(self, count: int = 1) -> None:
        self._total_archives += count

    def record_restore(self, count: int = 1) -> None:
        self._total_restores += count

    def get_total_entries_cleaned(self) -> int:
        return sum(self._entries_cleaned)

    def get_avg_search_latency(self) -> float:
        if not self._search_latencies:
            return 0.0
        return round(sum(self._search_latencies) / len(self._search_latencies), 2)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_cleanups": self._total_cleanups,
            "total_merges": self._total_merges,
            "total_optimizations": self._total_optimizations,
            "total_searches": self._total_searches,
            "total_archives": self._total_archives,
            "total_restores": self._total_restores,
            "total_entries_cleaned": self.get_total_entries_cleaned(),
            "avg_search_latency_ms": self.get_avg_search_latency(),
        }

    def reset(self) -> None:
        self._total_cleanups = 0
        self._total_merges = 0
        self._total_optimizations = 0
        self._total_searches = 0
        self._total_archives = 0
        self._total_restores = 0
        self._entries_cleaned.clear()
        self._entries_merged.clear()
        self._search_latencies.clear()
