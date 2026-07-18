"""storage_router.py — Routes data to correct storage."""
from __future__ import annotations
from typing import Any, Dict


class StorageRouter:
    """Routes data operations to appropriate storage backends."""

    def __init__(self) -> None:
        self._routes: Dict[str, str] = {}
        self._backends: Dict[str, Any] = {}
        self._default: str = "memory"

    def register_backend(self, name: str, backend: Any) -> None:
        self._backends[name] = backend

    def route(self, data_type: str, backend: str) -> None:
        self._routes[data_type] = backend

    def get_backend(self, data_type: str) -> str:
        return self._routes.get(data_type, self._default)

    def set_default(self, backend: str) -> None:
        self._default = backend

    def get_backend_instance(self, data_type: str) -> Any:
        backend_name = self.get_backend(data_type)
        return self._backends.get(backend_name)

    def list_routes(self) -> Dict[str, str]:
        return dict(self._routes)

    def stats(self) -> Dict[str, Any]:
        return {"routes": len(self._routes), "backends": len(self._backends)}
