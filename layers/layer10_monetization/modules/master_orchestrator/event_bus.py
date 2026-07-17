"""Event Bus — System-wide event publishing and subscribing."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List

_EB_COUNTER = itertools.count(1)


class SystemEvent:
    """A system-wide event."""

    __slots__ = ("event_id", "event_type", "source", "data", "timestamp")

    def __init__(self, event_type: str = "", source: str = "") -> None:
        self.event_id: str = f"evt_{next(_EB_COUNTER)}"
        self.event_type = event_type
        self.source = source
        self.data: Dict[str, Any] = {}
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
        }


class SystemEventBus:
    """Publish and subscribe to system events."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_log: List[SystemEvent] = []

    def publish(self, event: SystemEvent) -> int:
        self._event_log.append(event)
        handlers = self._subscribers.get(event.event_type, [])
        for h in handlers:
            try:
                h(event)
            except Exception:
                pass
        return len(handlers)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                return True
            except ValueError:
                pass
        return False

    def get_events(self, event_type: str = "", limit: int = 50) -> List[SystemEvent]:
        events = self._event_log
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def get_event_count(self, event_type: str = "") -> int:
        if event_type:
            return sum(1 for e in self._event_log if e.event_type == event_type)
        return len(self._event_log)

    @property
    def subscriber_count(self) -> int:
        return sum(len(h) for h in self._subscribers.values())
