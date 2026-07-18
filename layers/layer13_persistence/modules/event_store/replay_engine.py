"""replay_engine.py — Event replay engine."""
from __future__ import annotations
from typing import Any, Callable, Dict, List
from layers.layer13_persistence.modules.event_store.event import Event


class ReplayEngine:
    """Replays events to rebuild aggregate state."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable] = {}
        self._replay_count: int = 0

    def register_handler(self, event_type: str, handler: Callable) -> None:
        self._handlers[event_type] = handler

    def replay(self, events: List[Event], initial_state: Dict[str, Any] = None) -> Dict[str, Any]:
        state = dict(initial_state or {})
        for event in events:
            handler = self._handlers.get(event.event_type)
            if handler:
                state = handler(state, event)
            self._replay_count += 1
        return state

    def replay_aggregate(self, aggregate_id: str, events: List[Event],
                          initial_state: Dict[str, Any] = None) -> Dict[str, Any]:
        agg_events = [e for e in events if e.aggregate_id == aggregate_id]
        return self.replay(agg_events, initial_state)

    def get_replay_count(self) -> int:
        return self._replay_count

    def stats(self) -> Dict[str, Any]:
        return {"handlers": len(self._handlers), "replays": self._replay_count}
