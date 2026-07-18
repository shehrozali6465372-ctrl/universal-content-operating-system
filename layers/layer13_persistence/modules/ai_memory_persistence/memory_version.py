"""memory_version.py — Memory versioning."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class MemoryVersion:
    """Version of a memory entry."""
    __slots__ = ("version_id", "key", "value", "created_at", "is_current")
    _counter = 0

    def __init__(self, key: str, value: Any) -> None:
        MemoryVersion._counter += 1
        self.version_id: int = MemoryVersion._counter
        self.key = key
        self.value = value
        self.created_at: float = time.time()
        self.is_current: bool = True


class MemoryVersionManager:
    """Manages memory version history."""

    def __init__(self) -> None:
        self._versions: Dict[str, List[MemoryVersion]] = {}

    def create_version(self, key: str, value: Any) -> MemoryVersion:
        if key not in self._versions:
            self._versions[key] = []
        for v in self._versions[key]:
            v.is_current = False
        version = MemoryVersion(key, value)
        self._versions[key].append(version)
        return version

    def get_current(self, key: str) -> Optional[MemoryVersion]:
        versions = self._versions.get(key, [])
        for v in reversed(versions):
            if v.is_current:
                return v
        return versions[-1] if versions else None

    def get_history(self, key: str) -> List[MemoryVersion]:
        return list(self._versions.get(key, []))

    def rollback(self, key: str, version_id: int) -> bool:
        versions = self._versions.get(key, [])
        for v in versions:
            if v.version_id == version_id:
                for other in versions:
                    other.is_current = False
                v.is_current = True
                return True
        return False

    def total_versions(self) -> int:
        return sum(len(v) for v in self._versions.values())

    def stats(self) -> Dict[str, Any]:
        return {"keys": len(self._versions), "total_versions": self.total_versions()}
