"""AdaptivePlanner — Modify plans during execution."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_ADPL_COUNTER = itertools.count(1)


class AdaptationEvent:
    """A plan adaptation event."""

    __slots__ = ("event_id", "plan_id", "reason", "changes",
                 "trigger", "timestamp")

    def __init__(self, plan_id: str = "", reason: str = "") -> None:
        self.event_id: str = f"adapt_{next(_ADPL_COUNTER)}"
        self.plan_id = plan_id
        self.reason = reason
        self.changes: List[Dict[str, Any]] = []
        self.trigger: str = ""
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id, "plan_id": self.plan_id,
            "reason": self.reason, "trigger": self.trigger,
        }


class AdaptivePlanner:
    """Adapt execution plans based on real-time feedback."""

    def __init__(self) -> None:
        self._adaptations: List[AdaptationEvent] = []
        self._active_plan_id: Optional[str] = None

    def set_plan(self, plan_id: str) -> None:
        self._active_plan_id = plan_id

    def adapt_on_failure(self, plan_id: str, failed_layer: str,
                         error: str) -> AdaptationEvent:
        event = AdaptationEvent(plan_id, f"Failure in {failed_layer}: {error}")
        event.trigger = "failure"
        event.changes.append({"action": "skip_or_retry", "layer": failed_layer})
        self._adaptations.append(event)
        return event

    def adapt_on_analytics(self, plan_id: str, metric: str,
                            value: float) -> AdaptationEvent:
        event = AdaptationEvent(plan_id, f"Analytics: {metric}={value}")
        event.trigger = "analytics"
        if value < 0.3:
            event.changes.append({"action": "adjust_strategy", "metric": metric})
        elif value > 0.8:
            event.changes.append({"action": "scale_up", "metric": metric})
        self._adaptations.append(event)
        return event

    def adapt_on_timeout(self, plan_id: str, layer: str) -> AdaptationEvent:
        event = AdaptationEvent(plan_id, f"Timeout in {layer}")
        event.trigger = "timeout"
        event.changes.append({"action": "increase_timeout", "layer": layer})
        self._adaptations.append(event)
        return event

    def get_adaptations(self, plan_id: str = "") -> List[AdaptationEvent]:
        if plan_id:
            return [a for a in self._adaptations if a.plan_id == plan_id]
        return list(self._adaptations)

    def get_stats(self) -> Dict[str, Any]:
        triggers = {}
        for a in self._adaptations:
            triggers[a.trigger] = triggers.get(a.trigger, 0) + 1
        return {"total_adaptations": len(self._adaptations), "by_trigger": triggers}
