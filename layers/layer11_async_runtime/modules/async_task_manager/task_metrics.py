"""Thread-safe task metrics."""
from __future__ import annotations

import threading
from typing import Any, Dict


class TaskMetrics:
    def __init__(self) -> None:
        self._data: Dict[str, int] = {
            "submitted": 0, "completed": 0, "failed": 0, "cancelled": 0
        }
        self._lock = threading.RLock()

    def record(self, metric: str, value: int = 1) -> None:
        if not metric:
            raise ValueError("metric must be non-empty")
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("value must be an integer")
        with self._lock:
            self._data[metric] = self._data.get(metric, 0) + value

    def get(self, metric: str) -> int:
        with self._lock:
            return self._data.get(metric, 0)

    def get_success_rate(self) -> float:
        with self._lock:
            total = self._data.get("completed", 0) + self._data.get("failed", 0)
            return round(self._data.get("completed", 0) / total, 3) if total else 0.0

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data)
