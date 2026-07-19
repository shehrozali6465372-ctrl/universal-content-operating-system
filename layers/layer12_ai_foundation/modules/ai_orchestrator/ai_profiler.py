"""AIProfiler — profile orchestrator performance."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class AIProfiler:
    def __init__(self) -> None:
        self._profiles: List[Dict[str, Any]] = []
    def record(self, op: str, ms: float) -> None: self._profiles.append({"op": op, "ms": ms, "ts": time.time()})
    def get_avg(self, op: str) -> float:
        ops = [p for p in self._profiles if p["op"] == op]
        return sum(o["ms"] for o in ops) / max(len(ops), 1)
    def summary(self) -> Dict[str, Any]:
        return {"count": len(self._profiles), "total_ms": round(sum(p["ms"] for p in self._profiles), 2)}
    def clear(self) -> None: self._profiles.clear()
