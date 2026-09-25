"""EventStream — bounded in-process event bus with observable handler failures."""
from __future__ import annotations

import itertools
import threading
import time
from typing import Any, Callable, Dict, List, Optional

_ES_COUNTER = itertools.count(1)


class Event:
    """A system event."""

    def __init__(self, event_type: str, source: str = "") -> None:
        self.event_id = f"evt_{next(_ES_COUNTER)}"
        self.event_type = event_type
        self.source = source
        self.data: Dict[str, Any] = {}
        self.timestamp = time.time()
        self.handled = False
        self.handler_errors: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "type": self.event_type,
            "source": self.source,
            "timestamp": self.timestamp,
            "handled": self.handled,
            "handler_errors": list(self.handler_errors),
        }


class EventStream:
    """Global event bus with bounded history and isolated handler failures."""

    def __init__(self, max_events: int = 10000) -> None:
        if max_events <= 0:
            raise ValueError("max_events must be positive")
        self._max_events = max_events
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._events: List[Event] = []
        self._global_handlers: List[Callable[[Event], None]] = []
        self._lock = threading.RLock()

    def publish(
        self,
        event_type: str,
        source: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> Event:
        event = Event(event_type, source)
        event.data = dict(data or {})
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                del self._events[:-self._max_events]
            handlers = list(self._subscribers.get(event_type, []))
            handlers.extend(self._global_handlers)
        for handler in handlers:
            try:
                handler(event)
                event.handled = True
            except Exception as exc:
                event.handler_errors.append(type(exc).__name__)
        return event

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        if not callable(handler):
            raise ValueError("handler must be callable")
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(handler)

    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        if not callable(handler):
            raise ValueError("handler must be callable")
        with self._lock:
            self._global_handlers.append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> bool:
        with self._lock:
            handlers = self._subscribers.get(event_type, [])
            if handler not in handlers:
                return False
            handlers.remove(handler)
            if not handlers:
                self._subscribers.pop(event_type, None)
            return True

    def get_events(self, event_type: str = "", count: int = 50) -> List[Event]:
        if count <= 0:
            return []
        with self._lock:
            events = (
                self._events
                if not event_type
                else [e for e in self._events if e.event_type == event_type]
            )
            return list(events[-count:])

    def get_event_types(self) -> List[str]:
        with self._lock:
            return sorted({event.event_type for event in self._events})

    def clear_events(self) -> int:
        with self._lock:
            count = len(self._events)
            self._events.clear()
            return count

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            types: Dict[str, int] = {}
            errors = 0
            for event in self._events:
                types[event.event_type] = types.get(event.event_type, 0) + 1
                errors += len(event.handler_errors)
            return {
                "total_events": len(self._events),
                "by_type": types,
                "subscriber_count": sum(
                    len(handlers) for handlers in self._subscribers.values()
                ),
                "handler_errors": errors,
            }
