"""snapshot_manager.py — Snapshot management."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional


class Snapshot:
    """Aggregate snapshot."""
    __slots__ = ("aggregate_id", "version", "state", "created_at")
    _counter = 0

    def __init__(self, aggregate_id: str, version: int, state: Dict[str, Any]) -> None:
        Snapshot._counter += 1
        self.aggregate_id = aggregate_id
        self.version = version
        self.state = state
        self.created_at: float = time.time()


class SnapshotManager:
    """Manages aggregate snapshots for fast recovery."""

    def __init__(self, snapshot_interval: int = 100) -> None:
        self._snapshots: Dict[str, Snapshot] = {}
        self._interval = snapshot_interval

    def save(self, aggregate_id: str, version: int, state: Dict[str, Any]) -> Snapshot:
        snap = Snapshot(aggregate_id, version, state)
        self._snapshots[aggregate_id] = snap
        return snap

    def get(self, aggregate_id: str) -> Optional[Snapshot]:
        return self._snapshots.get(aggregate_id)

    def should_snapshot(self, aggregate_id: str, current_version: int) -> bool:
        snap = self._snapshots.get(aggregate_id)
        if not snap:
            return True
        return (current_version - snap.version) >= self._interval

    def delete(self, aggregate_id: str) -> bool:
        return self._snapshots.pop(aggregate_id, None) is not None

    def count(self) -> int:
        return len(self._snapshots)

    def stats(self) -> Dict[str, Any]:
        return {"snapshots": self.count(), "interval": self._interval}
