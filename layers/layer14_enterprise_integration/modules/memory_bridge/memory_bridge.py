"""MemoryBridge — shared memory bus for cross-layer data exchange."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional


class MemoryEntry:
    __slots__ = ("key", "value", "namespace", "created_at", "updated_at", "ttl", "metadata")

    def __init__(self, key: str, value: Any, namespace: str = "default",
                 ttl: Optional[float] = None) -> None:
        self.key = key
        self.value = value
        self.namespace = namespace
        self.created_at = time.time()
        self.updated_at = time.time()
        self.ttl = ttl
        self.metadata: Dict[str, Any] = {}

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return (time.time() - self.updated_at) > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "namespace": self.namespace,
                "created_at": self.created_at, "updated_at": self.updated_at,
                "expired": self.is_expired()}


class MemoryBridge:
    def __init__(self) -> None:
        self._store: Dict[str, MemoryEntry] = {}
        self._lock = threading.Lock()
        self._history: List[Dict[str, Any]] = []

    def _make_key(self, namespace: str, key: str) -> str:
        return f"{namespace}::{key}"

    def put(self, key: str, value: Any, namespace: str = "default",
            ttl: Optional[float] = None) -> None:
        full_key = self._make_key(namespace, key)
        with self._lock:
            self._store[full_key] = MemoryEntry(key, value, namespace, ttl)
            self._history.append({"action": "put", "key": key, "namespace": namespace,
                                  "time": time.time()})

    def get(self, key: str, namespace: str = "default") -> Any:
        full_key = self._make_key(namespace, key)
        entry = self._store.get(full_key)
        if entry and not entry.is_expired():
            return entry.value
        return None

    def has(self, key: str, namespace: str = "default") -> bool:
        full_key = self._make_key(namespace, key)
        entry = self._store.get(full_key)
        return entry is not None and not entry.is_expired()

    def delete(self, key: str, namespace: str = "default") -> bool:
        full_key = self._make_key(namespace, key)
        with self._lock:
            if full_key in self._store:
                del self._store[full_key]
                self._history.append({"action": "delete", "key": key,
                                      "namespace": namespace, "time": time.time()})
                return True
        return False

    def list_keys(self, namespace: str = "default") -> List[str]:
        return [e.key for e in self._store.values()
                if e.namespace == namespace and not e.is_expired()]

    def list_namespaces(self) -> List[str]:
        return list(set(e.namespace for e in self._store.values()))

    def clear_namespace(self, namespace: str) -> int:
        with self._lock:
            keys_to_delete = [k for k, e in self._store.items() if e.namespace == namespace]
            for k in keys_to_delete:
                del self._store[k]
            return len(keys_to_delete)

    def clear_all(self) -> int:
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    def cleanup_expired(self) -> int:
        with self._lock:
            expired = [k for k, e in self._store.items() if e.is_expired()]
            for k in expired:
                del self._store[k]
            return len(expired)

    def count(self, namespace: Optional[str] = None) -> int:
        if namespace:
            return len([e for e in self._store.values() if e.namespace == namespace])
        return len(self._store)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
