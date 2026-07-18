"""LoopMetrics — Track loop performance."""
from __future__ import annotations
from typing import Any, Dict

class LoopMetrics:
    def __init__(self) -> None:
        self._data: Dict[str, Any] = {"tasks_scheduled": 0, "tasks_completed": 0, "errors": 0}
    def record(self, metric: str, value: float = 1.0) -> None:
        self._data[metric] = self._data.get(metric, 0) + value
    def get(self, metric: str) -> float:
        return self._data.get(metric, 0.0)
    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)
    def reset(self) -> None:
        self._data = {"tasks_scheduled": 0, "tasks_completed": 0, "errors": 0}
