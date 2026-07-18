"""event.py — Event model."""
from __future__ import annotations
import time
from typing import Any, Dict


class Event:
    """Domain event."""
    __slots__ = ("event_id", "event_type", "aggregate_id", "aggregate_type",
                 "data", "metadata", "version", "timestamp")
    _counter = 0

    def __init__(self, event_type: str, aggregate_id: str, data: Dict[str, Any] = None,
                 aggregate_type: str = "") -> None:
        Event._counter += 1
        self.event_id: int = Event._counter
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.data = data or {}
        self.metadata: Dict[str, Any] = {}
        self.version: int = 0
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.event_id, "type": self.event_type,
                "aggregate_id": self.aggregate_id, "version": self.version,
                "data": dict(self.data)}
