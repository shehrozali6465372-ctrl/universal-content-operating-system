"""Checkpoint Manager — Save and restore workflow checkpoints."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_CM_COUNTER = itertools.count(1)


class Checkpoint:
    """A saved workflow checkpoint for recovery."""

    __slots__ = ("checkpoint_id", "workflow_id", "stage", "state",
                 "data", "created_at")

    def __init__(self, workflow_id: str = "", stage: str = "") -> None:
        self.checkpoint_id: str = f"cp_{next(_CM_COUNTER)}"
        self.workflow_id = workflow_id
        self.stage = stage
        self.state: Dict[str, Any] = {}
        self.data: Dict[str, Any] = {}
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "workflow_id": self.workflow_id,
            "stage": self.stage,
            "created_at": self.created_at,
        }


class CheckpointManager:
    """Manage workflow checkpoints for recovery and rollback."""

    def __init__(self, max_checkpoints: int = 50) -> None:
        self._max_checkpoints = max_checkpoints
        self._checkpoints: List[Checkpoint] = []

    def create(self, workflow_id: str, stage: str,
               state: Optional[Dict[str, Any]] = None,
               data: Optional[Dict[str, Any]] = None) -> Checkpoint:
        cp = Checkpoint(workflow_id, stage)
        if state:
            cp.state = dict(state)
        if data:
            cp.data = dict(data)
        self._checkpoints.append(cp)
        if len(self._checkpoints) > self._max_checkpoints:
            self._checkpoints = self._checkpoints[-self._max_checkpoints:]
        return cp

    def restore(self, checkpoint_id: str) -> Optional[Checkpoint]:
        for cp in self._checkpoints:
            if cp.checkpoint_id == checkpoint_id:
                return cp
        return None

    def get_latest(self, workflow_id: str = "") -> Optional[Checkpoint]:
        candidates = self._checkpoints
        if workflow_id:
            candidates = [cp for cp in candidates if cp.workflow_id == workflow_id]
        return candidates[-1] if candidates else None

    def delete(self, checkpoint_id: str) -> bool:
        for i, cp in enumerate(self._checkpoints):
            if cp.checkpoint_id == checkpoint_id:
                self._checkpoints.pop(i)
                return True
        return False

    def delete_workflow_checkpoints(self, workflow_id: str) -> int:
        before = len(self._checkpoints)
        self._checkpoints = [cp for cp in self._checkpoints if cp.workflow_id != workflow_id]
        return before - len(self._checkpoints)

    def get_all(self, workflow_id: str = "") -> List[Checkpoint]:
        if workflow_id:
            return [cp for cp in self._checkpoints if cp.workflow_id == workflow_id]
        return list(self._checkpoints)

    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._checkpoints)}
