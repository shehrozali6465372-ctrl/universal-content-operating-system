"""failover_manager.py — Failover management."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class FailoverEvent:
    """A failover event."""
    __slots__ = ("event_id", "from_node", "to_node", "reason", "timestamp", "success")
    _counter = 0

    def __init__(self, from_node: str, to_node: str, reason: str = "") -> None:
        FailoverEvent._counter += 1
        self.event_id: int = FailoverEvent._counter
        self.from_node = from_node
        self.to_node = to_node
        self.reason = reason
        self.timestamp: float = time.time()
        self.success: bool = True


class FailoverManager:
    """Manages failover between nodes."""

    def __init__(self) -> None:
        self._events: List[FailoverEvent] = []
        self._active_node: str = ""

    def set_active(self, node: str) -> None:
        self._active_node = node

    def trigger_failover(self, from_node: str, to_node: str,
                         reason: str = "") -> FailoverEvent:
        event = FailoverEvent(from_node, to_node, reason)
        self._events.append(event)
        self._active_node = to_node
        return event

    def get_active_node(self) -> str:
        return self._active_node

    def get_events(self) -> List[FailoverEvent]:
        return list(self._events)

    def stats(self) -> Dict[str, Any]:
        return {"active_node": self._active_node, "failovers": len(self._events)}
