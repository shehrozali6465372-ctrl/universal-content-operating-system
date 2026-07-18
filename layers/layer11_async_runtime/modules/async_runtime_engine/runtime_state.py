"""RuntimeState — Track runtime state transitions."""
from __future__ import annotations
import time
from typing import Dict, Any


class RuntimeState:
    """Runtime state machine."""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    RECOVERING = "recovering"
    ERROR = "error"

    VALID_TRANSITIONS = {
        CREATED: (STARTING,),
        STARTING: (RUNNING, ERROR),
        RUNNING: (PAUSED, STOPPING, ERROR),
        PAUSED: (RUNNING, STOPPING),
        STOPPING: (STOPPED, ERROR),
        STOPPED: (STARTING,),
        RECOVERING: (RUNNING, STOPPED, ERROR),
        ERROR: (RECOVERING, STOPPED),
    }

    __slots__ = ("_state", "_history", "_state_entered_at")

    def __init__(self) -> None:
        self._state = self.CREATED
        self._history: list[Dict[str, Any]] = []
        self._state_entered_at = time.time()

    @property
    def current(self) -> str:
        return self._state

    @property
    def uptime_in_state(self) -> float:
        return time.time() - self._state_entered_at

    def can_transition(self, new_state: str) -> bool:
        return new_state in self.VALID_TRANSITIONS.get(self._state, ())

    def transition(self, new_state: str) -> bool:
        if not self.can_transition(new_state):
            return False
        old = self._state
        self._state = new_state
        self._state_entered_at = time.time()
        self._history.append({"from": old, "to": new_state,
                               "timestamp": time.time()})
        return True

    def get_history(self, count: int = 10) -> list[Dict[str, Any]]:
        return self._history[-count:]

    def to_dict(self) -> Dict[str, Any]:
        return {"state": self._state, "uptime_in_state": round(self.uptime_in_state, 1),
                "transitions": len(self._history)}
