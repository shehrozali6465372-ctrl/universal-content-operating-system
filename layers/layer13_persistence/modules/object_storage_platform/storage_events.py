"""storage_events.py — Storage event system."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List


class StorageEvents:
    """Event system for storage operations."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._history: List[Dict[str, Any]] = []

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
        self._history.append({"event": event_type, "time": time.time()})
        return count

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history[-limit:]

    def stats(self) -> Dict[str, Any]:
        return {"event_types": len(self._handlers), "total_events": len(self._history)}
