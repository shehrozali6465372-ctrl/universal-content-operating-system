"""
Settings Event Bus
Layer 1: Core System — Module 9

Publish/subscribe event system for setting change notifications.
Other modules (Logger, Memory, Scheduler, etc.) subscribe to react to changes.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from threading import Lock


class SettingsEvent:
    """A single settings change event."""

    __slots__ = ("event_type", "key", "old_value", "new_value", "changed_by", "timestamp")

    def __init__(self, event_type: str, key: str, old_value: Any = None,
                 new_value: Any = None, changed_by: str = "system"):
        self.event_type = event_type
        self.key = key
        self.old_value = old_value
        self.new_value = new_value
        self.changed_by = changed_by
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
            "timestamp": self.timestamp,
        }


class SettingsEventBus:
    """Pub/sub event bus for settings change notifications."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
        self._event_log: List[dict] = []
        self._lock = Lock()
        self._max_log_size = 500

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to a specific setting change event."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable) -> None:
        """Subscribe to ALL setting change events."""
        with self._lock:
            self._global_subscribers.append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """Remove a specific subscription."""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                    return True
                except ValueError:
                    pass
        return False

    def emit(self, event: SettingsEvent) -> None:
        """Emit a settings change event to all relevant subscribers."""
        with self._lock:
            # Log the event
            self._event_log.append(event.to_dict())
            if len(self._event_log) > self._max_log_size:
                self._event_log = self._event_log[-self._max_log_size:]

        # Notify key-specific subscribers
        handlers = []
        with self._lock:
            handlers.extend(self._subscribers.get(event.event_type, []))
            handlers.extend(self._subscribers.get(event.key, []))
            handlers.extend(self._global_subscribers)

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass  # Don't let subscriber errors break the bus

    def get_event_log(self, key: Optional[str] = None,
                      event_type: Optional[str] = None,
                      limit: int = 50) -> List[dict]:
        """Get recent events with optional filtering."""
        with self._lock:
            events = list(self._event_log)
        if key:
            events = [e for e in events if e["key"] == key]
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        return events[-limit:]

    def clear_log(self) -> int:
        """Clear event log. Returns number of events cleared."""
        with self._lock:
            count = len(self._event_log)
            self._event_log.clear()
            return count

    def subscriber_count(self, event_type: Optional[str] = None) -> int:
        """Count subscribers. If event_type given, count for that type only."""
        with self._lock:
            if event_type:
                return len(self._subscribers.get(event_type, []))
            total = sum(len(v) for v in self._subscribers.values())
            total += len(self._global_subscribers)
            return total
