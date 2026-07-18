"""LoopProfiler — Profile loop operations."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LoopProfiler:
    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []
        self._active: Dict[str, float] = {}
    def start(self, operation: str) -> None:
        self._active[operation] = time.time()
    def stop(self, operation: str) -> float:
        start = self._active.pop(operation, 0.0)
        duration = (time.time() - start) * 1000
        self._entries.append({"operation": operation, "duration_ms": duration, "time": time.time()})
        return duration
    def get_entries(self, count: int = 20) -> List[Dict[str, Any]]:
        return self._entries[-count:]
    def get_stats(self) -> Dict[str, Any]:
        return {"total_entries": len(self._entries)}
