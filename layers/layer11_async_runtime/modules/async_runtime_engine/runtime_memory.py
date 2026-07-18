"""RuntimeMemory — Track runtime state for recovery."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class RuntimeCheckpoint:
    """A runtime checkpoint for recovery."""
    __slots__ = ("checkpoint_id", "state", "data", "created_at")

    def __init__(self, checkpoint_id: str = "", state: str = "") -> None:
        self.checkpoint_id = checkpoint_id
        self.state = state
        self.data: Dict[str, Any] = {}
        self.created_at: float = time.time()


class RuntimeMemory:
    """Store checkpoints and runtime history for recovery."""

    def __init__(self, max_checkpoints: int = 100) -> None:
        self._max = max_checkpoints
        self._checkpoints: List[RuntimeCheckpoint] = []

    def save_checkpoint(self, state: str, data: Dict[str, Any] = None) -> RuntimeCheckpoint:
        cp = RuntimeCheckpoint(f"cp_{len(self._checkpoints)}", state)
        if data:
            cp.data = dict(data)
        self._checkpoints.append(cp)
        if len(self._checkpoints) > self._max:
            self._checkpoints = self._checkpoints[-self._max:]
        return cp

    def get_latest(self) -> Optional[RuntimeCheckpoint]:
        return self._checkpoints[-1] if self._checkpoints else None

    def get_all(self) -> List[RuntimeCheckpoint]:
        return list(self._checkpoints)

    def clear(self) -> int:
        count = len(self._checkpoints)
        self._checkpoints.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        return {"total_checkpoints": len(self._checkpoints),
                "max_capacity": self._max}
