"""file_versioning.py — File versioning support."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class FileVersion:
    """A version of a file."""
    __slots__ = ("version_id", "bucket", "key", "size_bytes", "etag",
                 "created_at", "is_latest")
    _counter = 0

    def __init__(self, bucket: str, key: str, size_bytes: int, etag: str = "") -> None:
        FileVersion._counter += 1
        self.version_id: int = FileVersion._counter
        self.bucket = bucket
        self.key = key
        self.size_bytes = size_bytes
        self.etag = etag
        self.created_at: float = time.time()
        self.is_latest: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"version_id": self.version_id, "key": self.key,
                "size": self.size_bytes, "is_latest": self.is_latest}


class FileVersionManager:
    """Manages file versions."""

    def __init__(self) -> None:
        self._versions: Dict[str, List[FileVersion]] = {}

    def add_version(self, bucket: str, key: str, size_bytes: int,
                    etag: str = "") -> FileVersion:
        path = f"{bucket}/{key}"
        if path not in self._versions:
            self._versions[path] = []
        for v in self._versions[path]:
            v.is_latest = False
        version = FileVersion(bucket, key, size_bytes, etag)
        self._versions[path].append(version)
        return version

    def get_latest(self, bucket: str, key: str) -> Optional[FileVersion]:
        versions = self._versions.get(f"{bucket}/{key}", [])
        for v in reversed(versions):
            if v.is_latest:
                return v
        return versions[-1] if versions else None

    def get_all_versions(self, bucket: str, key: str) -> List[FileVersion]:
        return list(self._versions.get(f"{bucket}/{key}", []))

    def total_versions(self) -> int:
        return sum(len(v) for v in self._versions.values())
