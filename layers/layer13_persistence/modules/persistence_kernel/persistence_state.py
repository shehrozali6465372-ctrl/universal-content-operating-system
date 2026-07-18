"""persistence_state.py — Persistence system state."""
from __future__ import annotations
import time
from typing import Any, Dict


class PersistenceState:
    """Tracks persistence system state."""

    __slots__ = ("_state", "_sub_states", "_transitions", "_start_time")

    VALID_STATES = ("uninitialized", "initializing", "ready", "degraded",
                     "error", "shutting_down", "stopped")

    def __init__(self) -> None:
        self._state: str = "uninitialized"
        self._sub_states: Dict[str, str] = {}
        self._transitions: list = []
        self._start_time: float = 0.0

    def get_state(self) -> str:
        return self._state

    def set_state(self, new_state: str) -> bool:
        if new_state not in self.VALID_STATES:
            return False
        old = self._state
        self._state = new_state
        self._transitions.append({"from": old, "to": new_state, "time": time.time()})
        return True

    def set_sub_state(self, component: str, state: str) -> None:
        self._sub_states[component] = state

    def get_sub_state(self, component: str) -> str:
        return self._sub_states.get(component, "unknown")

    def get_all_sub_states(self) -> Dict[str, str]:
        return dict(self._sub_states)

    def is_ready(self) -> bool:
        return self._state == "ready"

    def get_transitions(self, limit: int = 50) -> list:
        return self._transitions[-limit:]

    def stats(self) -> Dict[str, Any]:
        return {"state": self._state, "sub_states": len(self._sub_states),
                "transitions": len(self._transitions)}
