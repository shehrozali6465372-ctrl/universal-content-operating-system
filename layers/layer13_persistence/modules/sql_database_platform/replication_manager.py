"""replication_manager.py — Database replication."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class ReplicaNode:
    """A replica node."""
    __slots__ = ("node_id", "host", "port", "role", "status", "lag_ms", "last_sync")
    _counter = 0

    def __init__(self, host: str, port: int = 5432, role: str = "replica") -> None:
        ReplicaNode._counter += 1
        self.node_id: int = ReplicaNode._counter
        self.host = host
        self.port = port
        self.role = role
        self.status: str = "synced"
        self.lag_ms: float = 0.0
        self.last_sync: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "host": self.host, "port": self.port,
                "role": self.role, "status": self.status}


class ReplicationManager:
    """Manages database replication."""

    def __init__(self) -> None:
        self._nodes: Dict[int, ReplicaNode] = {}
        self._is_enabled: bool = False

    def enable(self) -> None:
        self._is_enabled = True

    def disable(self) -> None:
        self._is_enabled = False

    def add_replica(self, node: ReplicaNode) -> bool:
        self._nodes[node.node_id] = node
        return True

    def remove_replica(self, node_id: int) -> bool:
        return self._nodes.pop(node_id, None) is not None

    def get_node(self, node_id: int) -> Optional[ReplicaNode]:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[ReplicaNode]:
        return list(self._nodes.values())

    def is_healthy(self) -> bool:
        return all(n.status == "synced" for n in self._nodes.values())

    def stats(self) -> Dict[str, Any]:
        statuses = {}
        for n in self._nodes.values():
            statuses[n.status] = statuses.get(n.status, 0) + 1
        return {"enabled": self._is_enabled, "nodes": len(self._nodes),
                "statuses": statuses}
