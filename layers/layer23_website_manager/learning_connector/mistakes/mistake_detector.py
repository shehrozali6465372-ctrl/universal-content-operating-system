"""MistakeDetector — Detect failures, low performance, and errors."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.learning_connector.models.learning_models import (
    MistakeRecord, LearningEvent,
)


class MistakeDetector:
    """Detect mistakes and failures across modules."""

    def __init__(self) -> None:
        self._mistakes: List[MistakeRecord] = []
        self._lock = threading.RLock()

    def record_mistake(self, module: str, mistake_type: str,
                       severity: str = "medium", description: str = "",
                       context: Optional[Dict] = None) -> MistakeRecord:
        mistake = MistakeRecord(module, mistake_type, severity, description, context)
        with self._lock:
            self._mistakes.append(mistake)
        return mistake

    def get_mistakes(self, module: Optional[str] = None,
                     severity: Optional[str] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            mistakes = self._mistakes
            if module:
                mistakes = [m for m in mistakes if m.module == module]
            if severity:
                mistakes = [m for m in mistakes if m.severity == severity]
            return [m.to_dict() for m in mistakes[-limit:]]

    def mark_resolved(self, mistake_id: str) -> bool:
        with self._lock:
            for m in self._mistakes:
                if m.mistake_id == mistake_id:
                    m.resolved = True
                    return True
            return False

    def detect_from_events(self, events: List[LearningEvent]) -> List[MistakeRecord]:
        detected = []
        for event in events:
            if not event.success:
                mistake = self.record_mistake(
                    module=event.module,
                    mistake_type="failed_event",
                    severity="high" if event.score == 0 else "medium",
                    description=f"Failed event: {event.event_type}",
                    context={"score": event.score, "metadata": event.metadata},
                )
                detected.append(mistake)
            elif event.score < 0.3 and event.score > 0:
                mistake = self.record_mistake(
                    module=event.module,
                    mistake_type="low_score",
                    severity="medium",
                    description=f"Low score: {event.score} for {event.event_type}",
                    context={"score": event.score},
                )
                detected.append(mistake)
        return detected

    def get_unresolved_count(self) -> int:
        with self._lock:
            return sum(1 for m in self._mistakes if not m.resolved)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._mistakes)
            unresolved = sum(1 for m in self._mistakes if not m.resolved)
            by_severity = {}
            for m in self._mistakes:
                by_severity[m.severity] = by_severity.get(m.severity, 0) + 1
            return {
                "total_mistakes": total,
                "unresolved": unresolved,
                "resolved": total - unresolved,
                "by_severity": by_severity,
            }
