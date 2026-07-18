"""storage_balancer.py — Storage load balancing."""
from __future__ import annotations
from typing import Any, Dict, List


class StorageBalancer:
    """Balances load across storage backends."""

    def __init__(self) -> None:
        self._backends: Dict[str, Dict[str, Any]] = {}
        self._distributions: List[Dict[str, Any]] = []

    def register(self, name: str, capacity: int = 100) -> None:
        self._backends[name] = {"capacity": capacity, "current": 0}

    def distribute(self, store_name: str, data: Any) -> str:
        selected = min(self._backends.keys(),
                        key=lambda k: self._backends[k]["current"])
        self._backends[selected]["current"] += 1
        self._distributions.append({"store": store_name, "backend": selected})
        return selected

    def get_load(self, backend: str) -> Dict[str, Any]:
        return dict(self._backends.get(backend, {}))

    def get_all_loads(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self._backends.items()}

    def stats(self) -> Dict[str, Any]:
        return {"backends": len(self._backends), "distributions": len(self._distributions)}
