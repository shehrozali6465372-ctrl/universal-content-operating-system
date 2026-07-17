"""Workflow Events — Event types and bus for workflow lifecycle."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List

_WEV_COUNTER = itertools.count(1)

# Event type constants
EVENT_WORKFLOW_STARTED = "workflow_started"
EVENT_STAGE_STARTED = "stage_started"
EVENT_STAGE_COMPLETED = "stage_completed"
EVENT_STAGE_FAILED = "stage_failed"
EVENT_STAGE_RETRIED = "stage_retried"
EVENT_WORKFLOW_PAUSED = "workflow_paused"
EVENT_WORKFLOW_RESUMED = "workflow_resumed"
EVENT_WORKFLOW_CANCELLED = "workflow_cancelled"
EVENT_WORKFLOW_COMPLETED = "workflow_completed"
EVENT_CHECKPOINT_CREATED = "checkpoint_created"


class WorkflowEvent:
    """A workflow lifecycle event."""

    __slots__ = ("event_id", "event_type", "workflow_id", "stage",
                 "data", "timestamp")

    def __init__(self, event_type: str = "", workflow_id: str = "") -> None:
        self.event_id: str = f"wevt_{next(_WEV_COUNTER)}"
        self.event_type = event_type
        self.workflow_id = workflow_id
        self.stage: str = ""
        self.data: Dict[str, Any] = {}
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "workflow_id": self.workflow_id,
            "stage": self.stage,
        }


class WorkflowEventBus:
    """Publish and subscribe to workflow events."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_log: List[WorkflowEvent] = []

    def publish(self, event: WorkflowEvent) -> int:
        self._event_log.append(event)
        handlers = self._subscribers.get(event.event_type, [])
        for h in handlers:
            try:
                h(event)
            except Exception:
                pass
        return len(handlers)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                return True
            except ValueError:
                pass
        return False

    def get_events(self, event_type: str = "", workflow_id: str = "",
                   limit: int = 50) -> List[WorkflowEvent]:
        events = self._event_log
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if workflow_id:
            events = [e for e in events if e.workflow_id == workflow_id]
        return events[-limit:]

    def get_event_count(self, event_type: str = "") -> int:
        if event_type:
            return sum(1 for e in self._event_log if e.event_type == event_type)
        return len(self._event_log)

    @property
    def subscriber_count(self) -> int:
        return sum(len(h) for h in self._subscribers.values())
