"""persistence_bootstrap.py — Bootstrap persistence system."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer13_persistence.modules.persistence_kernel.persistence_kernel import PersistenceKernel
from layers.layer13_persistence.modules.persistence_kernel.persistence_configuration import PersistenceConfiguration
from layers.layer13_persistence.modules.persistence_kernel.persistence_manager import PersistenceManager
from layers.layer13_persistence.modules.persistence_kernel.persistence_lifecycle import PersistenceLifecycle


class PersistenceBootstrap:
    """Bootstraps the entire persistence system."""

    __slots__ = ("_config", "_kernel", "_manager", "_lifecycle", "_bootstrapped")

    def __init__(self, config: Optional[PersistenceConfiguration] = None) -> None:
        self._config = config or PersistenceConfiguration()
        self._kernel = PersistenceKernel(self._config)
        self._manager = PersistenceManager(self._kernel)
        self._lifecycle = PersistenceLifecycle()
        self._bootstrapped = False

    def bootstrap(self) -> bool:
        if self._bootstrapped:
            return True
        self._manager.initialize()
        self._bootstrapped = True
        return True

    def shutdown(self) -> bool:
        if not self._bootstrapped:
            return True
        self._manager.shutdown()
        self._bootstrapped = False
        return True

    def register_store(self, name: str, store: Any) -> None:
        self._kernel.register_store(name, store)
        self._lifecycle.register(name, store)

    def get_kernel(self) -> PersistenceKernel:
        return self._kernel

    def get_manager(self) -> PersistenceManager:
        return self._manager

    def get_lifecycle(self) -> PersistenceLifecycle:
        return self._lifecycle

    def is_bootstrapped(self) -> bool:
        return self._bootstrapped

    def status(self) -> Dict[str, Any]:
        return {"bootstrapped": self._bootstrapped, "kernel": self._kernel.status(),
                "manager": self._manager.status()}
