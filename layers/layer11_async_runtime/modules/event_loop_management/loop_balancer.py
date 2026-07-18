"""LoopBalancer — Balance load across loops."""
from __future__ import annotations
from typing import Any, Dict

class LoopBalancer:
    def __init__(self) -> None:
        self._loop_loads: Dict[str, int] = {}
    def assign(self, loop_id: str) -> str:
        self._loop_loads[loop_id] = self._loop_loads.get(loop_id, 0) + 1
        return loop_id
    def release(self, loop_id: str) -> None:
        self._loop_loads[loop_id] = max(0, self._loop_loads.get(loop_id, 0) - 1)
    def get_balanced(self) -> str:
        if not self._loop_loads:
            return "default"
        return min(self._loop_loads, key=self._loop_loads.get)
    def get_stats(self) -> Dict[str, Any]:
        return {"loads": dict(self._loop_loads)}
