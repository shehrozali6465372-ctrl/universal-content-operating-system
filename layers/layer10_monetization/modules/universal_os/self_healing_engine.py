"""SelfHealingEngine — recovery planning without falsely claiming execution."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_SHE_COUNTER = itertools.count(1)
RECOVERY_ACTIONS = ("retry", "restart", "switch_endpoint", "rollback", "skip", "alert")


class HealingEvent:
    def __init__(self, failure_type: str, source: str) -> None:
        self.event_id = f"he_{next(_SHE_COUNTER)}"
        self.failure_type = failure_type
        self.source = source
        self.action = ""
        self.success = False
        self.message = ""
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "failure_type": self.failure_type,
                "source": self.source, "action": self.action,
                "success": self.success, "message": self.message}


class SelfHealingEngine:
    """Select a recovery action; execution is performed by an explicit executor."""

    def __init__(self) -> None:
        self._events: List[HealingEvent] = []
        self._failure_counts: Dict[str, int] = {}
        self._recovery_strategies: Dict[str, List[str]] = {
            "api_failure": ["retry", "switch_endpoint", "alert"],
            "plugin_failure": ["restart", "switch_endpoint", "rollback"],
            "worker_failure": ["restart", "skip", "alert"],
            "model_failure": ["switch_endpoint", "retry", "alert"],
        }

    def heal(self, failure_type: str, source: str,
             context: Optional[Dict[str, Any]] = None) -> HealingEvent:
        if not failure_type or not source:
            raise ValueError("failure_type and source are required")
        strategies = self._recovery_strategies.get(failure_type, ["retry", "alert"])
        if not strategies or any(action not in RECOVERY_ACTIONS for action in strategies):
            raise ValueError("recovery strategy contains an invalid action")
        event = HealingEvent(failure_type, source)
        count = self._failure_counts.get(failure_type, 0) + 1
        self._failure_counts[failure_type] = count
        index = min(max(count - 1, 0), len(strategies) - 1)
        event.action = strategies[index]
        event.message = f"Recovery action '{event.action}' selected (attempt {count})"
        self._events.append(event)
        return event

    def record_result(self, event_id: str, success: bool, message: str = "") -> bool:
        for event in reversed(self._events):
            if event.event_id == event_id:
                event.success = bool(success)
                if message:
                    event.message = message
                return True
        return False

    def register_strategy(self, failure_type: str, actions: List[str]) -> None:
        if not actions or any(action not in RECOVERY_ACTIONS for action in actions):
            raise ValueError("strategy must contain valid recovery actions")
        self._recovery_strategies[failure_type] = list(actions)

    def get_events(self, failure_type: str = "", count: int = 20) -> List[HealingEvent]:
        if count <= 0:
            return []
        events = self._events if not failure_type else [
            event for event in self._events if event.failure_type == failure_type
        ]
        return list(events[-count:])

    def get_failure_counts(self) -> Dict[str, int]:
        return dict(self._failure_counts)

    def reset_counts(self) -> None:
        self._failure_counts.clear()

    def get_stats(self) -> Dict[str, Any]:
        return {"total_healing_events": len(self._events),
                "success_count": sum(event.success for event in self._events),
                "failure_counts": dict(self._failure_counts)}
