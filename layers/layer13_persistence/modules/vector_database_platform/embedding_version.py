"""embedding_version.py — Embedding versioning."""
from __future__ import annotations
import time
from typing import Dict, List, Optional


class EmbeddingVersion:
    """Versioned embedding."""
    __slots__ = ("version_id", "model", "dimensions", "created_at")
    _counter = 0

    def __init__(self, model: str, dimensions: int) -> None:
        EmbeddingVersion._counter += 1
        self.version_id: int = EmbeddingVersion._counter
        self.model = model
        self.dimensions = dimensions
        self.created_at: float = time.time()


class EmbeddingVersionManager:
    """Manages embedding versions."""

    def __init__(self) -> None:
        self._versions: Dict[str, List[EmbeddingVersion]] = {}

    def add_version(self, model: str, dimensions: int) -> EmbeddingVersion:
        v = EmbeddingVersion(model, dimensions)
        if model not in self._versions:
            self._versions[model] = []
        self._versions[model].append(v)
        return v

    def get_latest(self, model: str) -> Optional[EmbeddingVersion]:
        versions = self._versions.get(model, [])
        return versions[-1] if versions else None

    def get_all(self, model: str) -> List[EmbeddingVersion]:
        return list(self._versions.get(model, []))

    def count(self) -> int:
        return sum(len(v) for v in self._versions.values())
