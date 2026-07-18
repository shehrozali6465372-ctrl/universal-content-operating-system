"""event_search.py — Event search."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.event_store.event import Event


class EventSearcher:
    """Searches events with various filters."""

    def __init__(self) -> None:
        self._indexed: Dict[str, List[int]] = {}

    def index(self, events: List[Event]) -> None:
        for event in events:
            for key in self._extract_keys(event):
                if key not in self._indexed:
                    self._indexed[key] = []
                self._indexed[key].append(event.event_id)

    def search(self, query: str, events: List[Event]) -> List[Event]:
        event_map = {e.event_id: e for e in events}
        matching_ids = set()
        for key, ids in self._indexed.items():
            if query.lower() in key.lower():
                matching_ids.update(ids)
        return [event_map[eid] for eid in matching_ids if eid in event_map]

    def _extract_keys(self, event: Event) -> List[str]:
        keys = [event.event_type, event.aggregate_type, event.aggregate_id]
        for v in event.data.values():
            if isinstance(v, str):
                keys.append(v)
        return keys

    def stats(self) -> Dict[str, Any]:
        return {"indexed_keys": len(self._indexed)}
