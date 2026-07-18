"""read_replica_manager.py — Read replica management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class ReadReplica:
    """A read replica node."""
    __slots__ = ("replica_id", "host", "port", "status", "lag_ms", "last_sync")
    _counter = 0

    def __init__(self, host: str, port: int = 5432) -> None:
        ReadReplica._counter += 1
        self.replica_id: int = ReadReplica._counter
        self.host = host
        self.port = port
        self.status: str = "synced"
        self.lag_ms: float = 0.0
        self.last_sync: float = time.time()


class ReadReplicaManager:
    """Manages read replicas."""

    def __init__(self) -> None:
        self._replicas: Dict[int, ReadReplica] = {}
        self._current_index: int = 0

    def add(self, host: str, port: int = 5432) -> ReadReplica:
        replica = ReadReplica(host, port)
        self._replicas[replica.replica_id] = replica
        return replica

    def remove(self, replica_id: int) -> bool:
        return self._replicas.pop(replica_id, None) is not None

    def get_next(self) -> Optional[ReadReplica]:
        healthy = [r for r in self._replicas.values() if r.status == "synced"]
        if not healthy:
            return None
        replica = healthy[self._current_index % len(healthy)]
        self._current_index += 1
        return replica

    def list_all(self) -> List[ReadReplica]:
        return list(self._replicas.values())

    def stats(self) -> Dict[str, Any]:
        return {"replicas": len(self._replicas),
                "healthy": sum(1 for r in self._replicas.values() if r.status == "synced")}
