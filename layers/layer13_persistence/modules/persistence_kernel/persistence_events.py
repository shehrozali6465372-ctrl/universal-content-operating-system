"""persistence_events.py — Event system for persistence."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List


class PersistenceEvent:
    """Single persistence event."""
    __slots__ = ("event_type", "data", "timestamp")

    def __init__(self, event_type: str, data: Dict[str, Any] = None) -> None:
        self.event_type = event_type
        self.data = data or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"event_type": self.event_type, "data": self.data,
                "timestamp": self.timestamp}


class PersistenceEvents:
    """Event bus for persistence system."""

    __slots__ = ("_handlers", "_history", "_max_history")

    def __init__(self, max_history: int = 10000) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._history: List[PersistenceEvent] = []
        self._max_history = max_history

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, data: Dict[str, Any] = None) -> PersistenceEvent:
        event = PersistenceEvent(event_type, data)
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception:
                pass
        for handler in self._handlers.get("*", []):
            try:
                handler(event)
            except Exception:
                pass
        return event

    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._history[-limit:]]

    def get_by_type(self, event_type: str) -> List[PersistenceEvent]:
        return [e for e in self._history if e.event_type == event_type]

    def clear(self) -> None:
        self._history.clear()

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for e in self._history:
            types[e.event_type] = types.get(e.event_type, 0) + 1
        return {"total": len(self._history), "by_type": types}
