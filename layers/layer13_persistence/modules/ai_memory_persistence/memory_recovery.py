"""memory_recovery.py — Memory recovery after crashes."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class RecoverySnapshot:
    """A memory recovery snapshot."""
    __slots__ = ("snapshot_id", "stores", "created_at", "metadata")
    _counter = 0

    def __init__(self, stores: Dict[str, Any]) -> None:
        RecoverySnapshot._counter += 1
        self.snapshot_id: int = RecoverySnapshot._counter
        self.stores = stores
        self.created_at: float = time.time()
        self.metadata: Dict[str, Any] = {}


class MemoryRecovery:
    """Handles memory recovery and snapshots."""

    def __init__(self) -> None:
        self._snapshots: Dict[int, RecoverySnapshot] = {}
        self._max_snapshots: int = 10

    def create_snapshot(self, stores: Dict[str, Any]) -> RecoverySnapshot:
        if len(self._snapshots) >= self._max_snapshots:
            oldest = min(self._snapshots.keys())
            del self._snapshots[oldest]
        snapshot = RecoverySnapshot(stores)
        self._snapshots[snapshot.snapshot_id] = snapshot
        return snapshot

    def get_latest_snapshot(self) -> Optional[RecoverySnapshot]:
        if not self._snapshots:
            return None
        latest_id = max(self._snapshots.keys())
        return self._snapshots[latest_id]

    def restore(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        snapshot = self._snapshots.get(snapshot_id)
        return snapshot.stores if snapshot else None

    def list_snapshots(self) -> List[RecoverySnapshot]:
        return list(self._snapshots.values())

    def snapshot_count(self) -> int:
        return len(self._snapshots)

    def stats(self) -> Dict[str, Any]:
        return {"snapshots": self.snapshot_count(), "max": self._max_snapshots}
