"""Learning Events — Define and manage learning system events."""
from __future__ import annotations
from typing import Any, Dict, List
from dataclasses import dataclass, field


@dataclass
class LearningSystemEvent:
    """An event emitted by the learning system."""
    event_type: str = ""
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0


# Event type constants
EVENT_LEARNING_STARTED = "learning_started"
EVENT_LEARNING_COMPLETED = "learning_completed"
EVENT_LEARNING_FAILED = "learning_failed"
EVENT_MODULE_COMPLETED = "module_completed"
EVENT_MODULE_FAILED = "module_failed"
EVENT_LESSON_LEARNED = "lesson_learned"
EVENT_IMPROVEMENT_SUGGESTED = "improvement_suggested"
EVENT_MISTAKE_DETECTED = "mistake_detected"
EVENT_PATTERN_DETECTED = "pattern_detected"
EVENT_CALIBRATION_UPDATED = "calibration_updated"
EVENT_PREDICTION_MADE = "prediction_made"
EVENT_MEMORY_EVOLVED = "memory_evolved"
EVENT_OPTIMIZATION_COMPLETED = "optimization_completed"


class LearningEventBus:
    """Simple event bus for learning events."""

    def __init__(self) -> None:
        self._events: List[LearningSystemEvent] = []
        self._subscribers: Dict[str, List[Any]] = {}

    def emit(self, event: LearningSystemEvent) -> None:
        self._events.append(event)
        handlers = self._subscribers.get(event.event_type, [])
        for h in handlers:
            try:
                h(event)
            except Exception:
                pass

    def subscribe(self, event_type: str, handler: Any) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def get_events(self, event_type: str = "", limit: int = 50) -> List[LearningSystemEvent]:
        events = self._events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def get_event_count(self, event_type: str = "") -> int:
        if event_type:
            return sum(1 for e in self._events if e.event_type == event_type)
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()
        self._subscribers.clear()
