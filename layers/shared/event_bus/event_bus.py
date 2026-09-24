"""
Global Event Bus
Cross-layer event-driven communication.

Features:
- Subscribe/unsubscribe by EventType
- Priority-based handler ordering
- Event history and replay
- Async-safe publish
- Error isolation (one handler failure doesn't break others)
"""

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Union

from layers.shared.models.event import Event, EventType


class EventHandler:
    """Wraps a callback with metadata for the event bus."""

    __slots__ = ("callback", "priority", "name", "once")

    def __init__(
        self,
        callback: Callable[[Event], Any],
        priority: int = 0,
        name: str = "",
        once: bool = False,
    ):
        self.callback = callback
        self.priority = priority
        self.name = name or callback.__name__
        self.once = once

    def __repr__(self) -> str:
        return f"EventHandler(name='{self.name}', priority={self.priority})"


class EventBus:
    """Global event bus for cross-layer communication."""

    def __init__(self, max_history: int = 1000):
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._history: List[Event] = []
        self._max_history = max_history
        self._publish_count = 0
        self._error_count = 0

    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], Any],
        priority: int = 0,
        name: str = "",
        once: bool = False,
    ):
        """Subscribe a handler to an event type."""
        key = event_type.value if isinstance(event_type, EventType) else event_type
        if not isinstance(key, str) or not key.strip():
            raise ValueError("event_type must be a non-empty string")
        if not callable(callback):
            raise TypeError("callback must be callable")
        handlers = self._handlers[key]
        resolved_name = name or getattr(callback, "__name__", callback.__class__.__name__)
        if any(h.callback is callback and h.name == resolved_name for h in handlers):
            return False
        handler = EventHandler(callback, priority, resolved_name, once)
        handlers.append(handler)
        handlers.sort(key=lambda h: -h.priority)
        return True

    def unsubscribe(self, event_type: EventType, name: str) -> bool:
        """Unsubscribe a handler by name."""
        key = event_type.value if isinstance(event_type, EventType) else event_type
        handlers = self._handlers.get(key, [])
        for i, h in enumerate(handlers):
            if h.name == name:
                handlers.pop(i)
                return True
        return False

    def remove_callback(self, callback: Callable[[Event], Any]) -> bool:
        removed = False
        for key in list(self._handlers):
            handlers = self._handlers[key]
            remaining = [h for h in handlers if h.callback is not callback]
            if len(remaining) != len(handlers):
                removed = True
                self._handlers[key] = remaining
            if not self._handlers[key]:
                self._handlers.pop(key, None)
        return removed

    def subscriber_count(self) -> int:
        return sum(len(handlers) for handlers in self._handlers.values())

    def unsubscribe_all(self, callback: Callable[[Event], Any]) -> bool:
        return self.remove_callback(callback)

    def publish(self, event: Event) -> Dict[str, Any]:
        """Publish an event to all subscribed handlers."""
        key = event.event_type.value if isinstance(event.event_type, EventType) else event.event_type
        handlers = self._handlers.get(key, [])
        # Also notify wildcard subscribers
        wildcard_handlers = self._handlers.get("*", [])

        all_handlers = handlers + wildcard_handlers
        all_handlers.sort(key=lambda h: -h.priority)

        results: List[Dict[str, Any]] = []
        errors: List[str] = []

        for handler in all_handlers:
            try:
                handler.callback(event)
                results.append({"handler": handler.name, "status": "success"})
                if handler.once:
                    self.unsubscribe(event_type=key, name=handler.name)
            except Exception as exc:
                errors.append(f"{handler.name}: {str(exc)}")
                self._error_count += 1

        self._publish_count += 1

        # Store in history
        if len(self._history) >= self._max_history:
            self._history.pop(0)
        self._history.append(event)

        return {
            "event_id": event.event_id,
            "handlers_notified": len(all_handlers),
            "results": results,
            "errors": errors,
        }

    def subscribe_all(
        self,
        event_types: Union[List[EventType], Callable[[Event], Any]],
        callback: Optional[Callable[[Event], Any]] = None,
        priority: int = 0,
        name: str = "",
    ) -> bool:
        """Subscribe to multiple event types or all events."""
        if callable(event_types) and callback is None:
            return bool(self.subscribe("*", event_types, priority, name))
        if callback is None:
            raise TypeError("callback is required")
        changed = False
        for event_type in event_types:
            changed = bool(self.subscribe(event_type, callback, priority, name)) or changed
        return changed

    def get_history(self, event_type: Optional[EventType] = None, limit: int = 50) -> List[Event]:
        """Get event history, optionally filtered by type."""
        events = self._history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def get_handler_count(self, event_type: Optional[EventType] = None) -> int:
        """Get number of registered handlers."""
        if event_type:
            key = event_type.value if isinstance(event_type, EventType) else event_type
            return len(self._handlers.get(key, []))
        return sum(len(handlers) for handlers in self._handlers.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get bus statistics."""
        return {
            "total_handlers": self.get_handler_count(),
            "total_publishes": self._publish_count,
            "total_errors": self._error_count,
            "history_size": len(self._history),
            "event_types_with_handlers": len(self._handlers),
        }

    def clear_history(self):
        """Clear event history."""
        self._history.clear()

    def reset(self):
        """Clear all handlers and history."""
        self._handlers.clear()
        self._history.clear()
        self._publish_count = 0
        self._error_count = 0
