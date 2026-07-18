"""RuntimeEvents — Event system for runtime lifecycle."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List

_RE_COUNTER = itertools.count(1)


class RuntimeEvent:
    """A runtime event."""
    __slots__ = ("event_id", "event_type", "source", "data", "timestamp")

    def __init__(self, event_type: str = "", source: str = "") -> None:
        self.event_id: str = f"re_{next(_RE_COUNTER)}"
        self.event_type = event_type
        self.source = source
        self.data: Dict[str, Any] = {}
        self.timestamp: float = time.time()


class RuntimeEvents:
    """Publish-subscribe event system for runtime."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}
        self._events: List[RuntimeEvent] = []

    def publish(self, event_type: str, source: str = "",
                data: Dict[str, Any] = None) -> RuntimeEvent:
        event = RuntimeEvent(event_type, source)
        if data:
            event.data = dict(data)
        self._events.append(event)
        for handler in self._subscribers.get(event_type, []):
            try:
                handler(event)
            except Exception:
                pass
        return event

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        handlers = self._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)
            return True
        return False

    def get_events(self, event_type: str = "", count: int = 50) -> List[RuntimeEvent]:
        events = self._events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-count:]

    def clear(self) -> int:
        count = len(self._events)
        self._events.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for e in self._events:
            types[e.event_type] = types.get(e.event_type, 0) + 1
        return {"total_events": len(self._events), "by_type": types}
