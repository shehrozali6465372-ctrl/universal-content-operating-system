"""LoopMonitor — Monitor event loop health."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LoopMonitor:
    def __init__(self) -> None:
        self._snapshots: List[Dict[str, Any]] = []
    def record(self, loop_id: str, metrics: Dict[str, Any]) -> None:
        self._snapshots.append({"loop_id": loop_id, "metrics": metrics, "time": time.time()})
        if len(self._snapshots) > 500:
            self._snapshots = self._snapshots[-500:]
    def get_history(self, loop_id: str = "", count: int = 10) -> List[Dict[str, Any]]:
        snaps = self._snapshots
        if loop_id:
            snaps = [s for s in snaps if s["loop_id"] == loop_id]
        return snaps[-count:]
    def get_stats(self) -> Dict[str, Any]:
        return {"total_snapshots": len(self._snapshots)}
