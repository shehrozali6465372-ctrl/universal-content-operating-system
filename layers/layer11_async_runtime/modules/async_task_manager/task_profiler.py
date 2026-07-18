"""TaskProfiler — Profile task execution time."""
from __future__ import annotations
import time
from typing import Any, Dict, List
class TaskProfiler:
    def __init__(self): self._profiles: List[Dict[str, Any]] = []
    def profile(self, task_id: str, duration_ms: float, metadata: Dict[str, Any] = None):
        self._profiles.append({"task_id": task_id, "duration_ms": duration_ms, "metadata": metadata or {}, "time": time.time()})
    def get_slowest(self, count: int=10) -> List[Dict[str, Any]]:
        return sorted(self._profiles, key=lambda p: p["duration_ms"], reverse=True)[:count]
    def get_stats(self) -> Dict[str, Any]:
        if not self._profiles: return {"count": 0, "avg_ms": 0.0}
        avg = sum(p["duration_ms"] for p in self._profiles) / len(self._profiles)
        return {"count": len(self._profiles), "avg_ms": round(avg, 2)}
