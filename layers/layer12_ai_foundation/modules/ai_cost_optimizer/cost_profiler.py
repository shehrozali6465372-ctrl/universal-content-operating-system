"""CostProfiler — profile cost performance."""
from __future__ import annotations
import time
from typing import Any, Dict, List
class CostProfiler:
    def __init__(self) -> None:
        self._profiles: List[Dict[str, Any]] = []
    def record(self, operation: str, elapsed_ms: float) -> None:
        self._profiles.append({"operation": operation, "elapsed_ms": elapsed_ms, "ts": time.time()})
    def get_avg(self, operation: str) -> float:
        ops = [p for p in self._profiles if p["operation"] == operation]
        return sum(o["elapsed_ms"] for o in ops) / max(len(ops), 1)
    def summary(self) -> Dict[str, Any]:
        return {"count": len(self._profiles), "total_ms": round(sum(p["elapsed_ms"] for p in self._profiles), 2)}
    def clear(self) -> None:
        self._profiles.clear()
