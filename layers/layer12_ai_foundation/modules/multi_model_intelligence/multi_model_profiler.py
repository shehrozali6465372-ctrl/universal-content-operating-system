"""MultiModelProfiler — profile performance of multi-model operations."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class MultiModelProfiler:
    """Profile performance of multi-model operations."""

    def __init__(self) -> None:
        self._profiles: List[Dict[str, Any]] = []
        self._active: Dict[str, float] = {}

    def start(self, operation: str) -> None:
        self._active[operation] = time.time()

    def stop(self, operation: str) -> float:
        start = self._active.pop(operation, time.time())
        elapsed_ms = (time.time() - start) * 1000
        self._profiles.append({"operation": operation, "elapsed_ms": elapsed_ms})
        return elapsed_ms

    def get_profile(self, operation: Optional[str] = None) -> List[Dict[str, Any]]:
        if operation:
            return [p for p in self._profiles if p["operation"] == operation]
        return list(self._profiles)

    def summary(self) -> Dict[str, Any]:
        if not self._profiles:
            return {"count": 0, "total_ms": 0, "avg_ms": 0}
        total = sum(p["elapsed_ms"] for p in self._profiles)
        return {
            "count": len(self._profiles),
            "total_ms": round(total, 2),
            "avg_ms": round(total / len(self._profiles), 2),
        }

    def clear(self) -> None:
        self._profiles.clear()
