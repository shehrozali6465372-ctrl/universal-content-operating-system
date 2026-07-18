"""event_metrics.py — Event metrics."""
from __future__ import annotations
from typing import Any, Dict


class EventMetrics:
    """Tracks event store metrics."""

    def __init__(self) -> None:
        self._appended: int = 0
        self._read: int = 0
        self._replayed: int = 0
        self._by_type: Dict[str, int] = {}

    def record_append(self, event_type: str) -> None:
        self._appended += 1
        self._by_type[event_type] = self._by_type.get(event_type, 0) + 1

    def record_read(self, count: int = 1) -> None:
        self._read += count

    def record_replay(self, count: int = 1) -> None:
        self._replayed += count

    def to_dict(self) -> Dict[str, Any]:
        return {"appended": self._appended, "read": self._read,
                "replayed": self._replayed, "by_type": dict(self._by_type)}
