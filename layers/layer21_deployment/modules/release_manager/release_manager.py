"""Release lifecycle management with guarded state transitions."""
from __future__ import annotations
import re
import time
import uuid
from enum import Enum
from typing import Any, Dict, List

class ReleaseStatus(str, Enum):
    DRAFT = "draft"
    TESTING = "testing"
    RELEASED = "released"
    ROLLED_BACK = "rolled_back"

class Release:
    __slots__ = ("release_id", "version", "name", "status", "changes", "created_at", "released_at", "metadata")
    def __init__(self, version: str, name: str = "") -> None:
        if not re.fullmatch(r"v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
            raise ValueError("Release version must be semantic-version shaped")
        self.release_id = str(uuid.uuid4())
        self.version, self.name = version, name or f"Release {version}"
        self.status = ReleaseStatus.DRAFT
        self.changes: List[str] = []
        self.created_at, self.released_at = time.time(), 0.0
        self.metadata: Dict[str, Any] = {}
    def to_dict(self) -> Dict[str, Any]:
        return {"release_id": self.release_id, "version": self.version, "name": self.name,
                "status": self.status.value, "changes": list(self.changes),
                "created_at": self.created_at, "released_at": self.released_at}

class ReleaseManager:
    def __init__(self) -> None:
        self._releases: Dict[str, Release] = {}
        self._current_version = "0.0.0"
    def create_release(self, version: str, name: str = "") -> Release:
        if any(item.version == version for item in self._releases.values()):
            raise ValueError(f"Release already exists: {version}")
        release = Release(version, name)
        self._releases[release.release_id] = release
        return release
    def add_change(self, release_id: str, change: str) -> bool:
        release = self._releases.get(release_id)
        if release is None or release.status is not ReleaseStatus.DRAFT:
            return False
        if not change:
            raise ValueError("Release change cannot be empty")
        release.changes.append(change)
        return True
    def begin_testing(self, release_id: str) -> bool:
        release = self._releases.get(release_id)
        if release is None or release.status is not ReleaseStatus.DRAFT:
            return False
        release.status = ReleaseStatus.TESTING
        return True
    def release(self, release_id: str) -> bool:
        release = self._releases.get(release_id)
        if release is None or release.status is not ReleaseStatus.TESTING:
            return False
        release.status = ReleaseStatus.RELEASED
        release.released_at = time.time()
        self._current_version = release.version
        return True
    def rollback(self, release_id: str) -> bool:
        release = self._releases.get(release_id)
        if release is None or release.status is not ReleaseStatus.RELEASED:
            return False
        release.status = ReleaseStatus.ROLLED_BACK
        if self._current_version == release.version:
            prior = [r for r in self._releases.values()
                     if r.status is ReleaseStatus.RELEASED and r.version != release.version]
            self._current_version = max(prior, key=lambda r: r.released_at).version if prior else "0.0.0"
        return True
    def get_current_version(self) -> str:
        return self._current_version
    def list_releases(self) -> List[Dict[str, Any]]:
        return [release.to_dict() for release in self._releases.values()]
