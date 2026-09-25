"""Thread-safe bounded runtime state machine."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List


class RuntimeState:
    """Thread-safe state machine with bounded transition history."""

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

    __slots__ = (
        "_state", "_history", "_state_entered_at",
        "_state_entered_mono", "_lock", "_max_history",
    )

    def __init__(self, max_history: int = 1_000) -> None:
        if isinstance(max_history, bool) or not isinstance(max_history, int):
            raise TypeError("max_history must be an integer")
        if max_history < 1:
            raise ValueError("max_history must be >= 1")
        self._state = self.CREATED
        self._history: List[Dict[str, Any]] = []
        self._state_entered_at = time.time()
        self._state_entered_mono = time.monotonic()
        self._lock = threading.RLock()
        self._max_history = max_history

    @property
    def current(self) -> str:
        with self._lock:
            return self._state

    @property
    def uptime_in_state(self) -> float:
        with self._lock:
            return max(0.0, time.monotonic() - self._state_entered_mono)

    def can_transition(self, new_state: str) -> bool:
        if not isinstance(new_state, str):
            return False
        with self._lock:
            return new_state in self.VALID_TRANSITIONS.get(self._state, ())

    def transition(self, new_state: str) -> bool:
        if not isinstance(new_state, str):
            return False
        with self._lock:
            if new_state not in self.VALID_TRANSITIONS.get(self._state, ()):
                return False
            old = self._state
            now = time.time()
            self._state = new_state
            self._state_entered_at = now
            self._state_entered_mono = time.monotonic()
            self._history.append({"from": old, "to": new_state, "timestamp": now})
            if len(self._history) > self._max_history:
                del self._history[:-self._max_history]
            return True

    def get_history(self, count: int = 10) -> List[Dict[str, Any]]:
        if isinstance(count, bool) or not isinstance(count, int):
            raise TypeError("count must be an integer")
        if count < 0:
            raise ValueError("count must be >= 0")
        with self._lock:
            return list(self._history[-count:]) if count else []

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "state": self._state,
                "uptime_in_state": round(max(0.0, time.monotonic() - self._state_entered_mono), 1),
                "transitions": len(self._history),
            }
