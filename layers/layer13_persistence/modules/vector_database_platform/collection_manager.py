"""collection_manager.py — Vector collection management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class VectorCollection:
    """A named collection of vectors."""
    __slots__ = ("name", "dimensions", "metadata", "created_at", "record_count")
    _counter = 0

    def __init__(self, name: str, dimensions: int = 1536) -> None:
        VectorCollection._counter += 1
        self.name = name
        self.dimensions = dimensions
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.record_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "dimensions": self.dimensions,
                "record_count": self.record_count}


class CollectionManager:
    """Manages vector collections."""

    def __init__(self) -> None:
        self._collections: Dict[str, VectorCollection] = {}

    def create(self, name: str, dimensions: int = 1536) -> VectorCollection:
        col = VectorCollection(name, dimensions)
        self._collections[name] = col
        return col

    def delete(self, name: str) -> bool:
        return self._collections.pop(name, None) is not None

    def get(self, name: str) -> Optional[VectorCollection]:
        return self._collections.get(name)

    def list_all(self) -> List[VectorCollection]:
        return list(self._collections.values())

    def list_names(self) -> List[str]:
        return list(self._collections.keys())

    def count(self) -> int:
        return len(self._collections)

    def stats(self) -> Dict[str, Any]:
        return {"collections": self.count(),
                "total_records": sum(c.record_count for c in self._collections.values())}
