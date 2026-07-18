"""snapshot_engine.py — System snapshot engine."""
from __future__ import annotations
import time
from typing import Any, Dict


class SystemSnapshot:
    """System state snapshot."""
    __slots__ = ("snapshot_id", "state", "created_at", "size_bytes")
    _counter = 0

    def __init__(self, state: Dict[str, Any]) -> None:
        SystemSnapshot._counter += 1
        self.snapshot_id: int = SystemSnapshot._counter
        self.state = state
        self.created_at: float = time.time()
        self.size_bytes: int = len(str(state))


class SnapshotEngine:
    """Takes and manages system snapshots."""

    def __init__(self, max_snapshots: int = 50) -> None:
        self._snapshots: Dict[int, SystemSnapshot] = {}
        self._max = max_snapshots

    def take_snapshot(self, state: Dict[str, Any]) -> SystemSnapshot:
        snap = SystemSnapshot(state)
        self._snapshots[snap.snapshot_id] = snap
        if len(self._snapshots) > self._max:
            oldest = min(self._snapshots.keys())
            del self._snapshots[oldest]
        return snap

    def get_latest(self) -> SystemSnapshot:
        if not self._snapshots:
            return None
        return self._snapshots[max(self._snapshots.keys())]

    def restore(self, snapshot_id: int) -> Dict[str, Any]:
        snap = self._snapshots.get(snapshot_id)
        return snap.state if snap else {}

    def count(self) -> int:
        return len(self._snapshots)
