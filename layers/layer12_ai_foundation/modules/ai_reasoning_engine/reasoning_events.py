"""ReasoningEvents — event system for reasoning operations."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional


class ReasoningEvents:
    """Event bus for reasoning engine operations."""

    EVENT_TYPES = (
        "reasoning_started", "reasoning_completed", "reasoning_failed",
        "chain_verified", "chain_invalidated", "decision_made",
        "reflection_completed", "meta_analysis_done",
    )

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}
        self._log: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, callback: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [cb for cb in self._subscribers[event_type] if cb != callback]

    def publish(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        entry = {"event": event_type, "data": data or {}, "time": time.time()}
        self._log.append(entry)
        for cb in self._subscribers.get(event_type, []):
            try:
                cb(data or {})
            except Exception:
                pass

    def get_log(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if event_type:
            return [e for e in self._log if e["event"] == event_type]
        return list(self._log)

    def clear(self) -> None:
        self._log.clear()
