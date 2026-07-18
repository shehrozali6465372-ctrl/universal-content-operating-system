"""MultiModelEvents — event system for multi-model intelligence."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional


class MultiModelEvents:
    """Event bus for multi-model intelligence operations."""

    EVENT_TYPES = (
        "request_started", "request_completed", "request_failed",
        "model_responded", "model_failed", "consensus_reached",
        "vote_completed", "ranking_completed", "ensemble_completed",
    )

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_log: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, callback: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]

    def publish(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        entry = {"event": event_type, "data": data or {}, "time": time.time()}
        self._event_log.append(entry)
        for cb in self._subscribers.get(event_type, []):
            try:
                cb(data or {})
            except Exception:
                pass

    def get_log(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if event_type:
            return [e for e in self._event_log if e["event"] == event_type]
        return list(self._event_log)

    def clear_log(self) -> None:
        self._event_log.clear()
