"""SelfHealingEngine — Auto-recover from API, plugin, worker, and model failures."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_SHE_COUNTER = itertools.count(1)

RECOVERY_ACTIONS = ("retry", "restart", "switch_endpoint", "rollback", "skip", "alert")


class HealingEvent:
    """A self-healing event."""

    __slots__ = ("event_id", "failure_type", "source", "action",
                 "success", "message", "timestamp")

    def __init__(self, failure_type: str = "", source: str = "") -> None:
        self.event_id: str = f"he_{next(_SHE_COUNTER)}"
        self.failure_type = failure_type
        self.source = source
        self.action: str = ""
        self.success: bool = False
        self.message: str = ""
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "failure_type": self.failure_type,
                "source": self.source, "action": self.action,
                "success": self.success, "message": self.message}


class SelfHealingEngine:
    """Auto-recover from failures with retry, restart, switch, rollback."""

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
             context: Dict[str, Any] = None) -> HealingEvent:
        event = HealingEvent(failure_type, source)
        self._failure_counts[failure_type] = self._failure_counts.get(failure_type, 0) + 1
        strategies = self._recovery_strategies.get(failure_type, ["retry", "alert"])
        count = self._failure_counts[failure_type]
        if count <= 2:
            action = strategies[0] if strategies else "retry"
        elif count <= 5:
            action = strategies[1] if len(strategies) > 1 else "alert"
        else:
            action = strategies[-1] if strategies else "alert"
        event.action = action
        event.success = action in ("retry", "restart", "skip")
        event.message = f"Applied '{action}' for {failure_type} from {source} (attempt {count})"
        self._events.append(event)
        return event

    def register_strategy(self, failure_type: str,
                          actions: List[str]) -> None:
        self._recovery_strategies[failure_type] = list(actions)

    def get_events(self, failure_type: str = "",
                   count: int = 20) -> List[HealingEvent]:
        events = self._events
        if failure_type:
            events = [e for e in events if e.failure_type == failure_type]
        return events[-count:]

    def get_failure_counts(self) -> Dict[str, int]:
        return dict(self._failure_counts)

    def reset_counts(self) -> None:
        self._failure_counts.clear()

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._events)
        success = sum(1 for e in self._events if e.success)
        return {"total_healing_events": total, "success_count": success,
                "failure_counts": dict(self._failure_counts)}
