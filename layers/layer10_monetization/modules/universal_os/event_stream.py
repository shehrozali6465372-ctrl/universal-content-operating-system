"""EventStream — Global event bus for system-wide event publishing and subscribing."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List

_ES_COUNTER = itertools.count(1)

EVENT_TYPES = (
    "system_started", "system_stopped", "system_paused", "system_resumed",
    "content_created", "content_published", "content_failed",
    "quality_passed", "quality_failed",
    "publishing_started", "publishing_completed", "publishing_failed",
    "analytics_collected", "learning_completed", "optimization_applied",
    "revenue_updated", "trend_found", "opportunity_detected",
    "error_occurred", "recovery_triggered",
)


class Event:
    """A system event."""

    __slots__ = ("event_id", "event_type", "source", "data",
                 "timestamp", "handled")

    def __init__(self, event_type: str = "", source: str = "") -> None:
        self.event_id: str = f"evt_{next(_ES_COUNTER)}"
        self.event_type = event_type
        self.source = source
        self.data: Dict[str, Any] = {}
        self.timestamp: float = time.time()
        self.handled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "type": self.event_type,
                "source": self.source, "timestamp": self.timestamp}


class EventStream:
    """Global event bus — publish events, subscribe to event types."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}
        self._events: List[Event] = []
        self._global_handlers: List[Callable] = []

    def publish(self, event_type: str, source: str = "",
                data: Dict[str, Any] = None) -> Event:
        event = Event(event_type, source)
        if data:
            event.data = dict(data)
        self._events.append(event)
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers + self._global_handlers:
            try:
                handler(event)
                event.handled = True
            except Exception:
                pass
        return event

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def subscribe_all(self, handler: Callable) -> None:
        self._global_handlers.append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        handlers = self._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)
            return True
        return False

    def get_events(self, event_type: str = "", count: int = 50) -> List[Event]:
        events = self._events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-count:]

    def get_event_types(self) -> List[str]:
        return list(set(e.event_type for e in self._events))

    def clear_events(self) -> int:
        count = len(self._events)
        self._events.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for e in self._events:
            types[e.event_type] = types.get(e.event_type, 0) + 1
        return {"total_events": len(self._events), "by_type": types,
                "subscriber_count": sum(len(h) for h in self._subscribers.values())}
