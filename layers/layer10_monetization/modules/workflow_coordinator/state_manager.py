"""State Manager — Track workflow state with snapshots and rollback."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_SM_COUNTER = itertools.count(1)


class StateSnapshot:
    """A point-in-time snapshot of workflow state."""

    __slots__ = ("snapshot_id", "state", "current_stage", "completed_stages",
                 "timestamp", "metadata")

    def __init__(self) -> None:
        self.snapshot_id: str = f"snap_{next(_SM_COUNTER)}"
        self.state: str = "created"
        self.current_stage: str = ""
        self.completed_stages: List[str] = []
        self.timestamp: float = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "state": self.state,
            "current_stage": self.current_stage,
            "completed_stages": self.completed_stages,
        }


class StateManager:
    """Manage workflow state with snapshots and rollback."""

    VALID_STATES = ("created", "running", "paused", "waiting", "failed",
                    "completed", "cancelled", "rolled_back")

    def __init__(self) -> None:
        self._current_state: str = "created"
        self._current_stage: str = ""
        self._completed_stages: List[str] = []
        self._snapshots: List[StateSnapshot] = []
        self._state_history: List[Dict[str, Any]] = []

    def get_state(self) -> str:
        return self._current_state

    def set_state(self, state: str) -> bool:
        if state not in self.VALID_STATES:
            return False
        old_state = self._current_state
        self._current_state = state
        self._state_history.append({
            "from": old_state, "to": state, "timestamp": time.time(),
        })
        return True

    def set_current_stage(self, stage: str) -> None:
        self._current_stage = stage

    def complete_stage(self, stage: str) -> None:
        if stage not in self._completed_stages:
            self._completed_stages.append(stage)

    def get_completed_stages(self) -> List[str]:
        return list(self._completed_stages)

    def snapshot(self) -> StateSnapshot:
        snap = StateSnapshot()
        snap.state = self._current_state
        snap.current_stage = self._current_stage
        snap.completed_stages = list(self._completed_stages)
        self._snapshots.append(snap)
        return snap

    def restore(self, snapshot_id: str) -> bool:
        for snap in self._snapshots:
            if snap.snapshot_id == snapshot_id:
                self._current_state = snap.state
                self._current_stage = snap.current_stage
                self._completed_stages = list(snap.completed_stages)
                return True
        return False

    def rollback(self) -> bool:
        if self._snapshots:
            last = self._snapshots[-1]
            return self.restore(last.snapshot_id)
        return False

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._state_history)

    def get_snapshots(self) -> List[StateSnapshot]:
        return list(self._snapshots)

    def reset(self) -> None:
        self._current_state = "created"
        self._current_stage = ""
        self._completed_stages.clear()
        self._snapshots.clear()
        self._state_history.clear()
