"""provider_events.py — Provider event system."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List


class ProviderEvent:
    """Single provider event."""
    __slots__ = ("event_type", "provider", "data", "timestamp")

    def __init__(self, event_type: str, provider: str, data: Dict[str, Any] = None) -> None:
        self.event_type = event_type
        self.provider = provider
        self.data = data or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"event_type": self.event_type, "provider": self.provider,
                "data": self.data, "timestamp": self.timestamp}


class ProviderEvents:
    """Event bus for provider events."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._history: List[ProviderEvent] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]

    def publish(self, event_type: str, provider: str, data: Dict[str, Any] = None) -> ProviderEvent:
        event = ProviderEvent(event_type, provider, data)
        self._history.append(event)
        for handler in self._handlers.get(event_type, []):
            handler(event)
        for handler in self._handlers.get("*", []):
            handler(event)
        return event

    def get_history(self, provider: str = "", event_type: str = "") -> List[ProviderEvent]:
        events = self._history
        if provider:
            events = [e for e in events if e.provider == provider]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events

    def clear(self) -> None:
        self._history.clear()
