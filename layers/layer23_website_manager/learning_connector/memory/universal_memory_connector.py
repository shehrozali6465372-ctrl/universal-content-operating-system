"""UniversalMemoryConnector — Connect with Universal AI Memory."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.learning_connector.models.learning_models import MemoryRecord


class UniversalMemoryConnector:
    """Interface to Universal AI Memory system."""

    def __init__(self) -> None:
        self._store: Dict[str, MemoryRecord] = {}
        self._lock = threading.RLock()

    def store(self, key: str, value: Any, namespace: str = "default",
              ttl: Optional[float] = None,
              importance: float = 0.5) -> MemoryRecord:
        record = MemoryRecord(key, value, namespace, ttl, importance)
        with self._lock:
            self._store[record.memory_id] = record
        return record

    def retrieve(self, key: str, namespace: str = "default") -> Optional[Any]:
        now = time.time()
        with self._lock:
            for record in self._store.values():
                if record.key == key and record.namespace == namespace:
                    if record.ttl and (now - record.created_at) > record.ttl:
                        continue
                    return record.value
        return None

    def remember(self, key: str, namespace: str = "default") -> Optional[MemoryRecord]:
        now = time.time()
        with self._lock:
            for record in self._store.values():
                if record.key == key and record.namespace == namespace:
                    if record.ttl and (now - record.created_at) > record.ttl:
                        continue
                    return record
        return None

    def forget(self, key: str, namespace: str = "default") -> bool:
        with self._lock:
            for mem_id, record in list(self._store.items()):
                if record.key == key and record.namespace == namespace:
                    del self._store[mem_id]
                    return True
            return False

    def clear_namespace(self, namespace: str) -> int:
        count = 0
        with self._lock:
            for mem_id, record in list(self._store.items()):
                if record.namespace == namespace:
                    del self._store[mem_id]
                    count += 1
        return count

    def get_all_keys(self, namespace: str = "default") -> List[str]:
        with self._lock:
            return [
                r.key for r in self._store.values()
                if r.namespace == namespace
            ]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_records": len(self._store),
                "namespaces": len(set(r.namespace for r in self._store.values())),
            }
