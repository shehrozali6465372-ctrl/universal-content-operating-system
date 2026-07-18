"""persistence_manager.py — Universal persistence manager."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer13_persistence.modules.persistence_kernel.persistence_kernel import PersistenceKernel


class PersistenceManager:
    """Coordinates all persistence operations across the system."""

    __slots__ = ("_kernel", "_routers", "_stores", "_initialized")

    def __init__(self, kernel: Optional[PersistenceKernel] = None) -> None:
        self._kernel = kernel or PersistenceKernel()
        self._routers: Dict[str, str] = {}
        self._stores: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self) -> bool:
        self._kernel.start()
        self._initialized = True
        return True

    def shutdown(self) -> bool:
        self._kernel.stop()
        self._initialized = False
        return True

    def route(self, data_type: str, storage: str) -> bool:
        self._routers[data_type] = storage
        return True

    def get_route(self, data_type: str) -> str:
        return self._routers.get(data_type, "default")

    def store(self, data_type: str, key: str, data: Any) -> bool:
        storage = self.get_route(data_type)
        store = self._kernel.get_store(storage)
        if store:
            return store.set(key, data) if hasattr(store, "set") else True
        return False

    def retrieve(self, data_type: str, key: str) -> Optional[Any]:
        storage = self.get_route(data_type)
        store = self._kernel.get_store(storage)
        if store:
            return store.get(key) if hasattr(store, "get") else None
        return None

    def delete(self, data_type: str, key: str) -> bool:
        storage = self.get_route(data_type)
        store = self._kernel.get_store(storage)
        if store:
            return store.delete(key) if hasattr(store, "delete") else True
        return False

    def get_all_routes(self) -> Dict[str, str]:
        return dict(self._routers)

    def get_kernel(self) -> PersistenceKernel:
        return self._kernel

    def is_initialized(self) -> bool:
        return self._initialized

    def status(self) -> Dict[str, Any]:
        return {"initialized": self._initialized, "routes": len(self._routers),
                "kernel": self._kernel.status()}
