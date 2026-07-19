"""RepositoryRegistry — central registry for all data repositories."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class RepositoryRegistry:
    def __init__(self) -> None:
        self._repositories: Dict[str, Any] = {}

    def register(self, name: str, repository: Any) -> None:
        self._repositories[name] = repository

    def unregister(self, name: str) -> bool:
        if name in self._repositories:
            del self._repositories[name]
            return True
        return False

    def get(self, name: str) -> Optional[Any]:
        return self._repositories.get(name)

    def has(self, name: str) -> bool:
        return name in self._repositories

    def list_repositories(self) -> List[str]:
        return list(self._repositories.keys())

    def count(self) -> int:
        return len(self._repositories)
