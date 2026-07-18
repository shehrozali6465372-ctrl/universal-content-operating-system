"""MemoryMetrics — track memory system metrics."""
from __future__ import annotations

import time
from typing import Any, Dict


class MemoryMetrics:
    """Track metrics for the AI memory system."""

    def __init__(self) -> None:
        self.total_stores: int = 0
        self.total_retrievals: int = 0
        self.total_searches: int = 0
        self.total_hits: int = 0
        self.total_misses: int = 0
        self.total_evictions: int = 0
        self.total_syncs: int = 0
        self.total_latency_ms: float = 0.0
        self._start_time = time.time()

    def record_store(self) -> None:
        self.total_stores += 1

    def record_retrieval(self, hit: bool) -> None:
        self.total_retrievals += 1
        if hit:
            self.total_hits += 1
        else:
            self.total_misses += 1

    def record_search(self) -> None:
        self.total_searches += 1

    def record_eviction(self, count: int = 1) -> None:
        self.total_evictions += count

    def record_sync(self) -> None:
        self.total_syncs += 1

    def record_latency(self, ms: float) -> None:
        self.total_latency_ms += ms

    @property
    def hit_rate(self) -> float:
        total = self.total_hits + self.total_misses
        return self.total_hits / total if total > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        total_ops = self.total_stores + self.total_retrievals + self.total_searches
        return self.total_latency_ms / max(total_ops, 1)

    def reset(self) -> None:
        self.__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_stores": self.total_stores, "total_retrievals": self.total_retrievals,
            "total_searches": self.total_searches, "hit_rate": round(self.hit_rate, 4),
            "total_evictions": self.total_evictions, "total_syncs": self.total_syncs,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
        }
