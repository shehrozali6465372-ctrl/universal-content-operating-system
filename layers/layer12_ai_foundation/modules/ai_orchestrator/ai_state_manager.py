"""AIStateManager — manage orchestrator state."""
from __future__ import annotations
import time
from typing import Any, Dict

class AIStateManager:
    def __init__(self) -> None:
        self._state: Dict[str, Any] = {"status": "idle", "current_task": None}
        self._history: list = []
    def set(self, key: str, value: Any) -> None:
        self._state[key] = value
    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)
    def transition(self, new_status: str) -> None:
        old = self._state.get("status", "unknown")
        self._state["status"] = new_status
        self._history.append({"from": old, "to": new_status, "time": time.time()})
    def get_state(self) -> Dict[str, Any]:
        return dict(self._state)
    def get_history(self) -> list:
        return list(self._history)
    def reset(self) -> None:
        self._state = {"status": "idle", "current_task": None}; self._history.clear()
