"""RuntimeProfiler — Profile runtime performance."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class ProfileEntry:
    """A profiling entry."""
    __slots__ = ("operation", "duration_ms", "timestamp", "metadata")

    def __init__(self, operation: str = "", duration_ms: float = 0.0) -> None:
        self.operation = operation
        self.duration_ms = duration_ms
        self.timestamp: float = time.time()
        self.metadata: Dict[str, Any] = {}


class RuntimeProfiler:
    """Profile runtime operations for performance analysis."""

    def __init__(self) -> None:
        self._entries: List[ProfileEntry] = []
        self._active: Dict[str, float] = {}

    def start(self, operation: str) -> None:
        self._active[operation] = time.time()

    def stop(self, operation: str) -> float:
        start = self._active.pop(operation, None)
        if start is None:
            return 0.0
        duration = (time.time() - start) * 1000
        entry = ProfileEntry(operation, duration)
        self._entries.append(entry)
        return duration

    def get_entries(self, operation: str = "", count: int = 50) -> List[ProfileEntry]:
        entries = self._entries
        if operation:
            entries = [e for e in entries if e.operation == operation]
        return entries[-count:]

    def get_stats(self, operation: str = "") -> Dict[str, Any]:
        entries = self._entries
        if operation:
            entries = [e for e in entries if e.operation == operation]
        if not entries:
            return {"count": 0, "avg_ms": 0.0, "total_ms": 0.0}
        durations = [e.duration_ms for e in entries]
        return {"count": len(durations), "avg_ms": round(sum(durations) / len(durations), 2),
                "total_ms": round(sum(durations), 2), "min_ms": round(min(durations), 2),
                "max_ms": round(max(durations), 2)}

    def clear(self) -> int:
        count = len(self._entries)
        self._entries.clear()
        return count
