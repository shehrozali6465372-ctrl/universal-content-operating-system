"""LearningCollector — Collect learning data from all modules."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.learning_connector.models.learning_models import (
    LearningEvent,
)


class LearningCollector:
    """Collect learning data points from Modules 1-12."""

    def __init__(self) -> None:
        self._events: List[LearningEvent] = []
        self._lock = threading.RLock()
        self._max_events: int = 10000
        self._collected_by_module: Dict[str, int] = {}

    def collect(self, module: str, event_type: str, score: float = 0.0,
                metadata: Optional[Dict[str, Any]] = None,
                success: bool = True, source: str = "") -> LearningEvent:
        event = LearningEvent(module, event_type, score, metadata, success, source)
        with self._lock:
            self._events.append(event)
            self._collected_by_module[module] = self._collected_by_module.get(module, 0) + 1
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]
        return event

    def collect_from_all_modules(self,
                                  data: Dict[str, List[Dict[str, Any]]]) -> int:
        count = 0
        for module, events in data.items():
            for evt in events:
                self.collect(
                    module=module,
                    event_type=evt.get("event_type", "unknown"),
                    score=evt.get("score", 0.0),
                    metadata=evt.get("metadata"),
                    success=evt.get("success", True),
                    source=evt.get("source", ""),
                )
                count += 1
        return count

    def get_events(self, module: Optional[str] = None,
                   event_type: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            events = self._events
            if module:
                events = [e for e in events if e.module == module]
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return [e.to_dict() for e in events[-limit:]]

    def clear_events(self) -> int:
        with self._lock:
            count = len(self._events)
            self._events.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._events)
            successful = sum(1 for e in self._events if e.success)
            return {
                "total_events": total,
                "successful_events": successful,
                "failed_events": total - successful,
                "success_rate": round((successful / max(total, 1)) * 100, 1),
                "modules_active": len(self._collected_by_module),
                "events_by_module": dict(self._collected_by_module),
            }
