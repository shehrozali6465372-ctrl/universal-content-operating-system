"""event_bus.py — Global event bus for persistence."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List


class PersistenceEventBus:
    """Global event bus across all persistence modules."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._events: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, data: Dict[str, Any] = None) -> int:
        count = 0
        for handler in self._handlers.get(event_type, []):
            try:
                handler(data or {})
                count += 1
            except Exception:
                pass
        self._events.append({"event": event_type, "data": data or {},
                              "time": time.time()})
        return count

    def get_events(self, event_type: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        events = self._events
        if event_type:
            events = [e for e in events if e["event"] == event_type]
        return events[-limit:]

    def clear(self) -> int:
        count = len(self._events)
        self._events.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        return {"event_types": len(self._handlers), "total_events": len(self._events)}
