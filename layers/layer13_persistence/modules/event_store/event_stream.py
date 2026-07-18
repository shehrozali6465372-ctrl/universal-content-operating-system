"""event_stream.py — Event streaming."""
from __future__ import annotations
from typing import Any, Callable, Dict, List
from layers.layer13_persistence.modules.event_store.event import Event


class EventStream:
    """Real-time event streaming."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: List[Event] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: Event) -> int:
        self._history.append(event)
        count = 0
        for handler in self._subscribers.get(event.event_type, []):
            try:
                handler(event)
                count += 1
            except Exception:
                pass
        for handler in self._subscribers.get("*", []):
            try:
                handler(event)
                count += 1
            except Exception:
                pass
        return count

    def get_history(self, limit: int = 100) -> List[Event]:
        return self._history[-limit:]

    def clear_history(self) -> int:
        count = len(self._history)
        self._history.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        return {"total_events": len(self._history),
                "subscribers": len(self._subscribers)}
