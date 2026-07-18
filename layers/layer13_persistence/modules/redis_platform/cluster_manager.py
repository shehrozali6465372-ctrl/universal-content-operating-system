"""cluster_manager.py — Redis cluster management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class ClusterNode:
    """A Redis cluster node."""
    __slots__ = ("node_id", "host", "port", "role", "status", "slots", "last_heartbeat")
    _counter = 0

    def __init__(self, host: str, port: int = 6379, role: str = "master") -> None:
        ClusterNode._counter += 1
        self.node_id: int = ClusterNode._counter
        self.host = host
        self.port = port
        self.role = role
        self.status: str = "connected"
        self.slots: List[int] = []
        self.last_heartbeat: float = time.time()

    def is_healthy(self) -> bool:
        return self.status == "connected"

    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "host": self.host, "port": self.port,
                "role": self.role, "status": self.status}


class ClusterManager:
    """Manages a Redis cluster."""

    def __init__(self) -> None:
        self._nodes: Dict[int, ClusterNode] = {}
        self._is_cluster: bool = False

    def enable_cluster(self) -> None:
        self._is_cluster = True

    def disable_cluster(self) -> None:
        self._is_cluster = False

    def add_node(self, node: ClusterNode) -> bool:
        self._nodes[node.node_id] = node
        return True

    def remove_node(self, node_id: int) -> bool:
        return self._nodes.pop(node_id, None) is not None

    def get_node(self, node_id: int) -> Optional[ClusterNode]:
        return self._nodes.get(node_id)

    def get_masters(self) -> List[ClusterNode]:
        return [n for n in self._nodes.values() if n.role == "master"]

    def get_replicas(self) -> List[ClusterNode]:
        return [n for n in self._nodes.values() if n.role == "replica"]

    def is_healthy(self) -> bool:
        return all(n.is_healthy() for n in self._nodes.values())

    def stats(self) -> Dict[str, Any]:
        return {"cluster_enabled": self._is_cluster, "nodes": len(self._nodes),
                "masters": len(self.get_masters()), "replicas": len(self.get_replicas())}
