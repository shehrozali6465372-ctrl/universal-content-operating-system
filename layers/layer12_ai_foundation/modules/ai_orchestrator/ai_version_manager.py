"""AIVersionManager — manage orchestrator versioning and rollback."""
from __future__ import annotations
from typing import Any, Dict, List
import time

class AIVersionManager:
    def __init__(self, current_version: str = "1.0.0") -> None:
        self.current_version = current_version
        self._versions: List[Dict[str, Any]] = [{"version": current_version, "timestamp": time.time()}]
    def set_version(self, version: str) -> None:
        self.current_version = version
        self._versions.append({"version": version, "timestamp": time.time()})
    def rollback(self) -> str:
        if len(self._versions) > 1:
            self._versions.pop()
            self.current_version = self._versions[-1]["version"]
        return self.current_version
    def get_versions(self) -> List[Dict[str, Any]]:
        return list(self._versions)
    def get_current(self) -> str:
        return self.current_version
