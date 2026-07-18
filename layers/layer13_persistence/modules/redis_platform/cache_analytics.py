"""cache_analytics.py — Cache performance analytics."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class CacheAnalytics:
    """Tracks cache performance analytics."""

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []
        self._total_hits: int = 0
        self._total_misses: int = 0
        self._by_pattern: Dict[str, Dict[str, int]] = {}

    def record_hit(self, key: str, latency_ms: float = 0.0) -> None:
        self._total_hits += 1
        pattern = key.split(":")[0] if ":" in key else "default"
        if pattern not in self._by_pattern:
            self._by_pattern[pattern] = {"hits": 0, "misses": 0}
        self._by_pattern[pattern]["hits"] += 1
        self._events.append({"type": "hit", "key": key, "latency": latency_ms,
                              "time": time.time()})

    def record_miss(self, key: str, latency_ms: float = 0.0) -> None:
        self._total_misses += 1
        pattern = key.split(":")[0] if ":" in key else "default"
        if pattern not in self._by_pattern:
            self._by_pattern[pattern] = {"hits": 0, "misses": 0}
        self._by_pattern[pattern]["misses"] += 1
        self._events.append({"type": "miss", "key": key, "latency": latency_ms,
                              "time": time.time()})

    def get_hit_rate(self) -> float:
        total = self._total_hits + self._total_misses
        return self._total_hits / max(1, total)

    def get_pattern_stats(self) -> Dict[str, Dict[str, Any]]:
        result = {}
        for pattern, counts in self._by_pattern.items():
            total = counts["hits"] + counts["misses"]
            result[pattern] = {**counts, "hit_rate": counts["hits"] / max(1, total)}
        return result

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._events[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        return {"total_hits": self._total_hits, "total_misses": self._total_misses,
                "hit_rate": self.get_hit_rate(), "patterns": len(self._by_pattern)}
