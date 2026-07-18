"""persistence_clock.py — Logical clock for persistence."""
from __future__ import annotations
import time
from typing import Any, Dict


class PersistenceClock:
    """Logical clock for ordering persistence events."""

    def __init__(self) -> None:
        self._logical_time: int = 0
        self._wall_time: float = time.time()

    def tick(self) -> int:
        self._logical_time += 1
        self._wall_time = time.time()
        return self._logical_time

    def now(self) -> int:
        return self._logical_time

    def wall_time(self) -> float:
        return self._wall_time

    def update_if_greater(self, other_time: int) -> bool:
        if other_time > self._logical_time:
            self._logical_time = other_time
            return True
        return False

    def reset(self) -> None:
        self._logical_time = 0
        self._wall_time = time.time()

    def stats(self) -> Dict[str, Any]:
        return {"logical_time": self._logical_time}
