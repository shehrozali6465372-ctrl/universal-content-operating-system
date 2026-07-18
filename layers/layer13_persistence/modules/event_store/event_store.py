"""event_store.py — Core event store."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.event_store.event import Event


class EventStore:
    """Append-only event store with versioning."""

    def __init__(self) -> None:
        self._events: Dict[str, List[Event]] = {}
        self._global_events: List[Event] = []
        self._versions: Dict[str, int] = {}

    def append(self, event: Event) -> Event:
        agg_id = event.aggregate_id
        current_version = self._versions.get(agg_id, 0)
        event.version = current_version + 1
        self._versions[agg_id] = event.version
        if agg_id not in self._events:
            self._events[agg_id] = []
        self._events[agg_id].append(event)
        self._global_events.append(event)
        return event

    def get_events(self, aggregate_id: str) -> List[Event]:
        return list(self._events.get(aggregate_id, []))

    def get_events_from(self, aggregate_id: str, from_version: int = 0) -> List[Event]:
        return [e for e in self._events.get(aggregate_id, []) if e.version > from_version]

    def get_global_events(self, limit: int = 100) -> List[Event]:
        return self._global_events[-limit:]

    def get_events_by_type(self, event_type: str) -> List[Event]:
        return [e for e in self._global_events if e.event_type == event_type]

    def get_version(self, aggregate_id: str) -> int:
        return self._versions.get(aggregate_id, 0)

    def count(self, aggregate_id: str = "") -> int:
        if aggregate_id:
            return len(self._events.get(aggregate_id, []))
        return len(self._global_events)

    def aggregate_count(self) -> int:
        return len(self._events)

    def stats(self) -> Dict[str, Any]:
        return {"total_events": len(self._global_events),
                "aggregates": self.aggregate_count()}
