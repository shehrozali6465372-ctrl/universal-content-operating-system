"""ReleaseManager — version management and release tracking."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from enum import Enum


class ReleaseStatus(str, Enum):
    DRAFT = "draft"; TESTING = "testing"; RELEASED = "released"; ROLLED_BACK = "rolled_back"


class Release:
    __slots__ = ("release_id", "version", "name", "status", "changes",
                 "created_at", "released_at", "metadata")

    def __init__(self, version: str, name: str = "") -> None:
        self.release_id = str(uuid.uuid4())[:12]
        self.version = version
        self.name = name or f"Release {version}"
        self.status = ReleaseStatus.DRAFT
        self.changes: List[str] = []
        self.created_at = time.time()
        self.released_at: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"release_id": self.release_id, "version": self.version,
                "name": self.name, "status": self.status.value,
                "changes": len(self.changes)}


class ReleaseManager:
    def __init__(self) -> None:
        self._releases: Dict[str, Release] = {}
        self._current_version = "0.0.0"

    def create_release(self, version: str, name: str = "") -> Release:
        release = Release(version, name)
        self._releases[release.release_id] = release
        return release

    def add_change(self, release_id: str, change: str) -> bool:
        release = self._releases.get(release_id)
        if release:
            release.changes.append(change)
            return True
        return False

    def release(self, release_id: str) -> bool:
        release = self._releases.get(release_id)
        if release:
            release.status = ReleaseStatus.RELEASED
            release.released_at = time.time()
            self._current_version = release.version
            return True
        return False

    def rollback(self, release_id: str) -> bool:
        release = self._releases.get(release_id)
        if release:
            release.status = ReleaseStatus.ROLLED_BACK
            return True
        return False

    def get_current_version(self) -> str:
        return self._current_version

    def list_releases(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._releases.values()]
