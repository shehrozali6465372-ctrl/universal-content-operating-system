"""event_replication.py — Event replication."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.event_store.event import Event


class EventReplicator:
    """Replicates events across nodes."""

    def __init__(self) -> None:
        self._nodes: Dict[str, List[Event]] = {}
        self._replication_count: int = 0

    def register_node(self, node_id: str) -> None:
        self._nodes[node_id] = []

    def replicate(self, event: Event, node_ids: List[str] = None) -> int:
        targets = node_ids or list(self._nodes.keys())
        count = 0
        for node_id in targets:
            if node_id in self._nodes:
                self._nodes[node_id].append(event)
                count += 1
        self._replication_count += count
        return count

    def get_node_events(self, node_id: str) -> List[Event]:
        return list(self._nodes.get(node_id, []))

    def get_nodes(self) -> List[str]:
        return list(self._nodes.keys())

    def stats(self) -> Dict[str, Any]:
        return {"nodes": len(self._nodes), "replications": self._replication_count}
