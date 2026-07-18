"""replication_coordinator.py — Replication coordination."""
from __future__ import annotations
from typing import Any, Dict, List


class ReplicationCoordinator:
    """Coordinates replication across all stores."""

    def __init__(self) -> None:
        self._replications: Dict[str, List[str]] = {}
        self._replication_count: int = 0

    def register_store(self, store_name: str, replicas: List[str]) -> None:
        self._replications[store_name] = replicas

    def replicate(self, store_name: str) -> int:
        replicas = self._replications.get(store_name, [])
        self._replication_count += len(replicas)
        return len(replicas)

    def get_replicas(self, store_name: str) -> List[str]:
        return list(self._replications.get(store_name, []))

    def is_replicated(self, store_name: str) -> bool:
        return store_name in self._replications and len(self._replications[store_name]) > 0

    def stats(self) -> Dict[str, Any]:
        return {"stores": len(self._replications), "total_replications": self._replication_count}
