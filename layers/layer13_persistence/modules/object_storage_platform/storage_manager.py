"""storage_manager.py — Universal storage manager."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class StorageObject:
    """A stored object."""
    __slots__ = ("object_id", "bucket", "key", "size_bytes", "content_type",
                 "metadata", "created_at", "modified_at")
    _counter = 0

    def __init__(self, bucket: str, key: str, size_bytes: int = 0,
                 content_type: str = "application/octet-stream") -> None:
        StorageObject._counter += 1
        self.object_id: int = StorageObject._counter
        self.bucket = bucket
        self.key = key
        self.size_bytes = size_bytes
        self.content_type = content_type
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.modified_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.object_id, "bucket": self.bucket, "key": self.key,
                "size": self.size_bytes, "type": self.content_type}


class StorageManager:
    """Manages objects across multiple storage backends."""

    def __init__(self) -> None:
        self._objects: Dict[str, StorageObject] = {}
        self._backends: Dict[str, Any] = {}
        self._default_backend: str = "local"

    def register_backend(self, name: str, backend: Any) -> None:
        self._backends[name] = backend

    def put(self, bucket: str, key: str, data: bytes = b"",
            content_type: str = "application/octet-stream",
            metadata: Dict[str, Any] = None) -> StorageObject:
        obj = StorageObject(bucket, key, len(data), content_type)
        if metadata:
            obj.metadata = metadata
        self._objects[f"{bucket}/{key}"] = obj
        return obj

    def get(self, bucket: str, key: str) -> Optional[StorageObject]:
        return self._objects.get(f"{bucket}/{key}")

    def delete(self, bucket: str, key: str) -> bool:
        return self._objects.pop(f"{bucket}/{key}", None) is not None

    def list_objects(self, bucket: str, prefix: str = "") -> List[StorageObject]:
        prefix_full = f"{bucket}/{prefix}"
        return [o for k, o in self._objects.items()
                if k.startswith(prefix_full)]

    def exists(self, bucket: str, key: str) -> bool:
        return f"{bucket}/{key}" in self._objects

    def count(self, bucket: str = "") -> int:
        if bucket:
            return len([o for o in self._objects.values() if o.bucket == bucket])
        return len(self._objects)

    def total_size(self) -> int:
        return sum(o.size_bytes for o in self._objects.values())

    def stats(self) -> Dict[str, Any]:
        return {"objects": len(self._objects), "total_bytes": self.total_size(),
                "backends": len(self._backends)}
