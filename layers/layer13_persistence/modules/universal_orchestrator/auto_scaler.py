"""auto_scaler.py — Auto-scaling storage."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class AutoScaler:
    """Automatically scales storage capacity."""

    def __init__(self, min_capacity: int = 1, max_capacity: int = 100) -> None:
        self._min = min_capacity
        self._max = max_capacity
        self._current = min_capacity
        self._scale_events: List[Dict[str, Any]] = []

    def should_scale_up(self, utilization: float, threshold: float = 0.8) -> bool:
        return utilization > threshold and self._current < self._max

    def should_scale_down(self, utilization: float, threshold: float = 0.2) -> bool:
        return utilization < threshold and self._current > self._min

    def scale_up(self, factor: int = 1) -> int:
        old = self._current
        self._current = min(self._current + factor, self._max)
        self._scale_events.append({"direction": "up", "from": old,
                                    "to": self._current, "time": time.time()})
        return self._current

    def scale_down(self, factor: int = 1) -> int:
        old = self._current
        self._current = max(self._current - factor, self._min)
        self._scale_events.append({"direction": "down", "from": old,
                                    "to": self._current, "time": time.time()})
        return self._current

    def get_capacity(self) -> int:
        return self._current

    def get_events(self) -> List[Dict[str, Any]]:
        return list(self._scale_events)

    def stats(self) -> Dict[str, Any]:
        return {"current": self._current, "min": self._min, "max": self._max,
                "events": len(self._scale_events)}
