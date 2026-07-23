"""SlowQueryLogger — Detects and logs queries exceeding latency threshold.

Tracks total queries, slow count, average latency, p95, p99.
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional


class SlowQueryLogger:
    """Logs queries that exceed a configurable latency threshold."""

    def __init__(self, threshold_ms: float = 500.0):
        self._threshold_ms = threshold_ms
        self._slow_queries: List[Dict[str, Any]] = []
        self._total_queries = 0
        self._slow_count = 0
        self._latencies: List[float] = []
        self._lock = threading.Lock()
        self._max_slow = 1000

    def record(self, sql: str, latency_ms: float, params: tuple = ()) -> None:
        """Record a query execution. Log if slow."""
        with self._lock:
            self._total_queries += 1
            self._latencies.append(latency_ms)

            if latency_ms >= self._threshold_ms:
                self._slow_count += 1
                entry = {
                    "timestamp": time.time(),
                    "sql": sql[:500],
                    "latency_ms": round(latency_ms, 2),
                    "threshold_ms": self._threshold_ms,
                }
                self._slow_queries.append(entry)
                if len(self._slow_queries) > self._max_slow:
                    self._slow_queries = self._slow_queries[-self._max_slow:]

    def get_slow_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent slow queries."""
        with self._lock:
            return list(self._slow_queries[-limit:])

    def get_stats(self) -> Dict[str, Any]:
        """Return query performance statistics."""
        with self._lock:
            lats = self._latencies
            if not lats:
                return {
                    "total_queries": 0,
                    "slow_count": 0,
                    "slow_pct": 0.0,
                    "avg_latency_ms": 0.0,
                    "p95_ms": 0.0,
                    "p99_ms": 0.0,
                    "threshold_ms": self._threshold_ms,
                }
            sorted_lats = sorted(lats)
            avg = sum(lats) / len(lats)
            p95_idx = min(int(len(sorted_lats) * 0.95), len(sorted_lats) - 1)
            p99_idx = min(int(len(sorted_lats) * 0.99), len(sorted_lats) - 1)
            return {
                "total_queries": self._total_queries,
                "slow_count": self._slow_count,
                "slow_pct": round(self._slow_count / self._total_queries * 100, 2) if self._total_queries else 0.0,
                "avg_latency_ms": round(avg, 2),
                "p95_ms": round(sorted_lats[p95_idx], 2),
                "p99_ms": round(sorted_lats[p99_idx], 2),
                "threshold_ms": self._threshold_ms,
            }

    def reset(self) -> None:
        """Reset all counters."""
        with self._lock:
            self._slow_queries.clear()
            self._total_queries = 0
            self._slow_count = 0
            self._latencies.clear()
