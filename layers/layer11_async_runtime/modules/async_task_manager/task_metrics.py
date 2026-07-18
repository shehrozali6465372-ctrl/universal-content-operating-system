"""TaskMetrics — Track task performance."""
from __future__ import annotations
from typing import Any, Dict
class TaskMetrics:
    def __init__(self):
        self._data: Dict[str, Any] = {"submitted": 0, "completed": 0, "failed": 0, "cancelled": 0}
    def record(self, metric: str, value: int=1): self._data[metric] = self._data.get(metric, 0) + value
    def get(self, metric: str) -> int: return self._data.get(metric, 0)
    def get_success_rate(self) -> float:
        total = self._data.get("completed", 0) + self._data.get("failed", 0)
        return round(self._data.get("completed", 0) / max(1, total), 3)
    def to_dict(self) -> Dict[str, Any]: return dict(self._data)
