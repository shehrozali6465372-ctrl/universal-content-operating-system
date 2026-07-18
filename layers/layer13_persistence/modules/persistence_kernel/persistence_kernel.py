"""persistence_kernel.py — Core persistence kernel."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from layers.layer13_persistence.modules.persistence_kernel.persistence_configuration import PersistenceConfiguration
from layers.layer13_persistence.modules.persistence_kernel.persistence_health import PersistenceHealth
from layers.layer13_persistence.modules.persistence_kernel.persistence_metrics import PersistenceMetrics
from layers.layer13_persistence.modules.persistence_kernel.persistence_events import PersistenceEvents
from layers.layer13_persistence.modules.persistence_kernel.persistence_version import PersistenceVersion


class PersistenceKernel:
    """Brain of entire persistence system."""

    __slots__ = ("_config", "_health", "_metrics", "_events", "_version",
                 "_is_running", "_stores", "_start_time", "_registered_handlers")

    def __init__(self, config: Optional[PersistenceConfiguration] = None) -> None:
        self._config = config or PersistenceConfiguration()
        self._health = PersistenceHealth()
        self._metrics = PersistenceMetrics()
        self._events = PersistenceEvents()
        self._version = PersistenceVersion()
        self._is_running = False
        self._stores: Dict[str, Any] = {}
        self._start_time: float = 0.0
        self._registered_handlers: Dict[str, Callable] = {}

    def start(self) -> bool:
        if self._is_running:
            return True
        self._is_running = True
        self._start_time = time.time()
        self._health.mark_started()
        self._events.publish("kernel_started", {"config": self._config.to_dict()})
        return True

    def stop(self) -> bool:
        if not self._is_running:
            return True
        self._is_running = False
        self._health.mark_stopped()
        self._events.publish("kernel_stopped", {})
        return True

    def register_store(self, name: str, store: Any) -> bool:
        self._stores[name] = store
        self._metrics.record_store_registered(name)
        return True

    def unregister_store(self, name: str) -> bool:
        if name in self._stores:
            del self._stores[name]
            return True
        return False

    def get_store(self, name: str) -> Any:
        return self._stores.get(name)

    def get_all_stores(self) -> Dict[str, Any]:
        return dict(self._stores)

    def is_running(self) -> bool:
        return self._is_running

    def get_uptime(self) -> float:
        if not self._is_running:
            return 0.0
        return time.time() - self._start_time

    def get_health(self) -> Dict[str, Any]:
        return self._health.get_status(self._is_running, self._stores, self.get_uptime())

    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics.to_dict()

    def get_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._events.get_recent(limit)

    def get_version(self) -> Dict[str, Any]:
        return self._version.to_dict()

    def status(self) -> Dict[str, Any]:
        return {"running": self._is_running, "stores": len(self._stores),
                "uptime": self.get_uptime(), "health": self._health.to_dict(),
                "version": self._version.to_dict()}
