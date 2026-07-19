"""GovernanceProfiler — profile governance operations."""
from __future__ import annotations
from typing import Any, Dict, List

class GovernanceProfiler:
    def __init__(self) -> None:
        self._profiles: List[Dict[str, Any]] = []
    def record(self, op: str, ms: float) -> None: self._profiles.append({"op": op, "ms": ms})
    def summary(self) -> Dict[str, Any]:
        return {"count": len(self._profiles), "total_ms": round(sum(p["ms"] for p in self._profiles), 2)}
    def clear(self) -> None: self._profiles.clear()
