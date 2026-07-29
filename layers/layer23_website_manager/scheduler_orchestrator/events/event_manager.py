"""EventManager — Trigger and handle workflow events."""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import EventRecord


class EventManager:
    """Manage event emission and handling."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handlers: Dict[str, List[Callable]] = {}
        self._events: List[EventRecord] = []

    def register_handler(self, event_type: str, handler: Callable) -> None:
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)

    def unregister_handler(self, event_type: str, handler: Callable) -> bool:
        with self._lock:
            if event_type in self._handlers and handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                return True
            return False

    def emit(self, event_type: str, source: str = "",
             data: Optional[Dict[str, Any]] = None) -> EventRecord:
        event = EventRecord(event_type=event_type, source=source, data=data)
        with self._lock:
            self._events.append(event)
            handlers = list(self._handlers.get(event_type, []))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass
        return event

    def get_events(self, event_type: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            events = self._events
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return [e.to_dict() for e in events[-limit:]]

    def clear_events(self) -> int:
        with self._lock:
            count = len(self._events)
            self._events.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            event_types = {}
            for e in self._events:
                event_types[e.event_type] = event_types.get(e.event_type, 0) + 1
            return {
                "total_events": len(self._events),
                "registered_handlers": sum(len(h) for h in self._handlers.values()),
                "event_types": event_types,
            }
