"""replication_engine.py — Data replication."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class ReplicaNode:
    """Replica node."""
    __slots__ = ("node_id", "host", "status", "lag_ms", "last_sync")
    _counter = 0

    def __init__(self, host: str) -> None:
        ReplicaNode._counter += 1
        self.node_id: int = ReplicaNode._counter
        self.host = host
        self.status: str = "synced"
        self.lag_ms: float = 0.0
        self.last_sync: float = time.time()


class ReplicationEngine:
    """Manages data replication."""

    def __init__(self) -> None:
        self._nodes: Dict[int, ReplicaNode] = {}
        self._replicated_count: int = 0

    def add_node(self, host: str) -> ReplicaNode:
        node = ReplicaNode(host)
        self._nodes[node.node_id] = node
        return node

    def remove_node(self, node_id: int) -> bool:
        return self._nodes.pop(node_id, None) is not None

    def replicate(self, data: Any, target_nodes: List[int] = None) -> int:
        targets = target_nodes or list(self._nodes.keys())
        count = sum(1 for n in targets if n in self._nodes)
        self._replicated_count += count
        return count

    def is_healthy(self) -> bool:
        return all(n.status == "synced" for n in self._nodes.values())

    def get_nodes(self) -> List[ReplicaNode]:
        return list(self._nodes.values())

    def stats(self) -> Dict[str, Any]:
        return {"nodes": len(self._nodes), "replications": self._replicated_count}
