"""memory_snapshot.py — Memory snapshot management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class MemorySnapshotManager:
    """Manages periodic memory snapshots."""

    def __init__(self, interval_seconds: float = 300.0) -> None:
        self._interval = interval_seconds
        self._snapshots: List[Dict[str, Any]] = []
        self._last_snapshot: float = 0.0

    def should_snapshot(self) -> bool:
        return (time.time() - self._last_snapshot) >= self._interval

    def take_snapshot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = {"data": data, "timestamp": time.time(), "size": len(str(data))}
        self._snapshots.append(snapshot)
        self._last_snapshot = time.time()
        return snapshot

    def get_latest(self) -> Optional[Dict[str, Any]]:
        return self._snapshots[-1] if self._snapshots else None

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._snapshots)

    def clear(self) -> int:
        count = len(self._snapshots)
        self._snapshots.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        return {"snapshots": len(self._snapshots), "interval": self._interval}
