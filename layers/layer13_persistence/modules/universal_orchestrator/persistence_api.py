"""persistence_api.py — Universal persistence API."""
from __future__ import annotations
from typing import Any, Dict, Optional


class PersistenceAPI:
    """Unified API for all persistence operations."""

    def __init__(self) -> None:
        self._backends: Dict[str, Any] = {}
        self._request_count: int = 0
        self._error_count: int = 0

    def register_backend(self, name: str, backend: Any) -> None:
        self._backends[name] = backend

    def store(self, backend: str, key: str, value: Any) -> bool:
        self._request_count += 1
        b = self._backends.get(backend)
        if b and hasattr(b, "set"):
            return b.set(key, value)
        return False

    def retrieve(self, backend: str, key: str) -> Optional[Any]:
        self._request_count += 1
        b = self._backends.get(backend)
        if b and hasattr(b, "get"):
            return b.get(key)
        return None

    def delete(self, backend: str, key: str) -> bool:
        self._request_count += 1
        b = self._backends.get(backend)
        if b and hasattr(b, "delete"):
            result = b.delete(key)
            if isinstance(result, int):
                return result > 0
            return bool(result)
        return False

    def stats(self) -> Dict[str, Any]:
        return {"backends": len(self._backends), "requests": self._request_count,
                "errors": self._error_count}
