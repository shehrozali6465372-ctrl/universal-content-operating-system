"""Event Router — Route learning events to appropriate handlers."""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional


class LearningEvent:
    """A learning event to be routed."""

    __slots__ = ("event_type", "source_module", "data", "priority")

    def __init__(self, event_type: str = "", source_module: str = "",
                 data: Optional[Dict[str, Any]] = None) -> None:
        self.event_type = event_type
        self.source_module = source_module
        self.data: Dict[str, Any] = data if data is not None else {}
        self.priority: int = 0


class EventRouter:
    """Route events from learning modules to handlers."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._event_log: List[LearningEvent] = []

    def register(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def route(self, event: LearningEvent) -> int:
        self._event_log.append(event)
        handlers = self._handlers.get(event.event_type, [])
        for h in handlers:
            try:
                h(event)
            except Exception:
                pass
        return len(handlers)

    def get_handlers(self, event_type: str) -> List[Callable]:
        return list(self._handlers.get(event_type, []))

    def get_event_log(self, limit: int = 50) -> List[LearningEvent]:
        return list(self._event_log[-limit:])

    @property
    def event_count(self) -> int:
        return len(self._event_log)

    @property
    def handler_count(self) -> int:
        return sum(len(h) for h in self._handlers.values())
