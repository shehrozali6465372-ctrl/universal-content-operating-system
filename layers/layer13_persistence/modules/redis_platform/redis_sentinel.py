"""redis_sentinel.py — Redis Sentinel abstraction."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class SentinelNode:
    """Sentinel-managed node."""
    __slots__ = ("host", "port", "role", "status", "last_seen")
    _counter = 0

    def __init__(self, host: str, port: int, role: str = "replica") -> None:
        SentinelNode._counter += 1
        self.host = host
        self.port = port
        self.role = role
        self.status: str = "online"
        self.last_seen: float = time.time()


class RedisSentinel:
    """Redis Sentinel for high availability."""

    def __init__(self) -> None:
        self._sentinels: List[SentinelNode] = []
        self._master: Optional[SentinelNode] = None

    def add_sentinel(self, host: str, port: int) -> SentinelNode:
        node = SentinelNode(host, port, "sentinel")
        self._sentinels.append(node)
        return node

    def set_master(self, host: str, port: int) -> SentinelNode:
        self._master = SentinelNode(host, port, "master")
        return self._master

    def get_master(self) -> Optional[SentinelNode]:
        return self._master

    def get_replicas(self) -> List[SentinelNode]:
        return [n for n in self._sentinels if n.role == "replica"]

    def failover(self) -> bool:
        if self._master:
            self._master.status = "failed"
        replicas = self.get_replicas()
        if replicas:
            self._master = replicas[0]
            self._master.role = "master"
            return True
        return False

    def stats(self) -> Dict[str, Any]:
        return {"sentinels": len(self._sentinels),
                "master": self._master.host if self._master else None}
