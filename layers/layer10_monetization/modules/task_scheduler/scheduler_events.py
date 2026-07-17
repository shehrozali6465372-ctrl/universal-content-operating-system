"""Scheduler Events — Event types and bus for task scheduling."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List

_SEV_COUNTER = itertools.count(1)

EVENT_TASK_SCHEDULED = "task_scheduled"
EVENT_TASK_STARTED = "task_started"
EVENT_TASK_COMPLETED = "task_completed"
EVENT_TASK_FAILED = "task_failed"
EVENT_TASK_RETRIED = "task_retried"
EVENT_TASK_CANCELLED = "task_cancelled"
EVENT_QUEUE_FULL = "queue_full"
EVENT_WORKER_ASSIGNED = "worker_assigned"
EVENT_WORKER_RELEASED = "worker_released"


class SchedulerEvent:
    """A scheduler event."""

    __slots__ = ("event_id", "event_type", "task_id", "worker_id", "data", "timestamp")

    def __init__(self, event_type: str = "", task_id: str = "",
                 worker_id: str = "") -> None:
        self.event_id: str = f"sevt_{next(_SEV_COUNTER)}"
        self.event_type = event_type
        self.task_id = task_id
        self.worker_id = worker_id
        self.data: Dict[str, Any] = {}
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "task_id": self.task_id,
            "worker_id": self.worker_id,
        }


class SchedulerEventBus:
    """Publish and subscribe to scheduler events."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_log: List[SchedulerEvent] = []

    def publish(self, event: SchedulerEvent) -> int:
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

    def get_events(self, event_type: str = "", task_id: str = "",
                   limit: int = 50) -> List[SchedulerEvent]:
        events = self._event_log
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if task_id:
            events = [e for e in events if e.task_id == task_id]
        return events[-limit:]

    def get_event_count(self, event_type: str = "") -> int:
        if event_type:
            return sum(1 for e in self._event_log if e.event_type == event_type)
        return len(self._event_log)
