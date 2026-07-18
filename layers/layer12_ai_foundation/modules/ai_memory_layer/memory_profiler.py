"""MemoryProfiler — profile memory operation performance."""
from __future__ import annotations

import time
from typing import Any, Dict, List


class MemoryProfiler:
    """Profile performance of memory operations."""

    def __init__(self) -> None:
        self._profiles: List[Dict[str, Any]] = []

    def record(self, operation: str, elapsed_ms: float,
               entry_count: int = 0) -> None:
        self._profiles.append({"operation": operation, "elapsed_ms": elapsed_ms,
                                "entry_count": entry_count, "timestamp": time.time()})

    def get_avg(self, operation: str) -> float:
        ops = [p for p in self._profiles if p["operation"] == operation]
        return sum(o["elapsed_ms"] for o in ops) / max(len(ops), 1)

    def summary(self) -> Dict[str, Any]:
        if not self._profiles:
            return {"count": 0, "total_ms": 0.0}
        return {"count": len(self._profiles),
                "total_ms": round(sum(p["elapsed_ms"] for p in self._profiles), 2)}

    def clear(self) -> None:
        self._profiles.clear()
