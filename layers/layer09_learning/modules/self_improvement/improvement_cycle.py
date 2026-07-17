"""Improvement Cycle — Define and track improvement cycles."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict

_IC_COUNTER = itertools.count(1)

CYCLE_STATUSES = ("planned", "running", "completed", "failed", "rolled_back")
CYCLE_TYPES = ("mistake_fix", "optimization", "experiment", "calibration", "learning")


class ImprovementCycle:
    """A single improvement cycle with tracking."""

    __slots__ = ("cycle_id", "cycle_type", "status", "title", "description",
                 "start_time", "end_time", "duration_ms",
                 "improvements_made", "rollback_available", "metadata")

    def __init__(self, cycle_type: str = "optimization", title: str = "") -> None:
        self.cycle_id: str = f"icy_{next(_IC_COUNTER)}"
        self.cycle_type = cycle_type if cycle_type in CYCLE_TYPES else "optimization"
        self.status: str = "planned"
        self.title = title
        self.description: str = ""
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration_ms: float = 0.0
        self.improvements_made: int = 0
        self.rollback_available: bool = False
        self.metadata: Dict[str, Any] = {}

    def start(self) -> None:
        self.status = "running"
        self.start_time = time.time()

    def complete(self, improvements: int = 0) -> None:
        self.status = "completed"
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 1)
        self.improvements_made = improvements

    def fail(self, reason: str = "") -> None:
        self.status = "failed"
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 1)
        if reason:
            self.metadata["failure_reason"] = reason

    def rollback(self) -> None:
        if self.rollback_available:
            self.status = "rolled_back"

    @property
    def is_active(self) -> bool:
        return self.status == "running"

    @property
    def success(self) -> bool:
        return self.status == "completed" and self.improvements_made > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "cycle_type": self.cycle_type,
            "status": self.status,
            "title": self.title,
            "improvements_made": self.improvements_made,
            "duration_ms": self.duration_ms,
            "rollback_available": self.rollback_available,
        }
