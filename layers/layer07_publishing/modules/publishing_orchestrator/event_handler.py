"""Event Handler — Handle pipeline events via Event Bus."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List


class PipelineEvent:
    """A pipeline event."""

    __slots__ = ("event_type", "source", "data", "timestamp")

    def __init__(self, event_type: str = "", source: str = "") -> None:
        self.event_type = event_type
        self.source = source
        self.data: Dict[str, Any] = {}
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class EventHandler:
    """Handle pipeline events."""

    EVENT_TYPES = (
        "pipeline_started", "pipeline_completed", "pipeline_failed",
        "stage_started", "stage_completed", "stage_failed",
        "publish_started", "publish_completed", "publish_failed",
        "analytics_collected", "memory_updated",
    )

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._events: List[PipelineEvent] = []
        self._event_count = 0

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: PipelineEvent) -> None:
        self._events.append(event)
        self._event_count += 1
        for handler in self._handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception:
                pass

    def get_events(self, event_type: str = "") -> List[PipelineEvent]:
        if event_type:
            return [e for e in self._events if e.event_type == event_type]
        return list(self._events)

    @property
    def event_count(self) -> int:
        return self._event_count
