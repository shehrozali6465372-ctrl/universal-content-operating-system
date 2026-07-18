"""memory_repository.py — Memory repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class MemoryEntity(BaseEntity):
    __slots__ = ("memory_type", "key", "value", "confidence", "access_count")

    def __init__(self, memory_type: str, key: str, value: Any = None) -> None:
        super().__init__()
        self.memory_type = memory_type
        self.key = key
        self.value = value
        self.confidence: float = 1.0
        self.access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"type": self.memory_type, "key": self.key,
                      "confidence": self.confidence})
        return base


class MemoryRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("memory")

    def find_by_type(self, memory_type: str) -> List[MemoryEntity]:
        return self.find(memory_type=memory_type)

    def find_by_key(self, key: str) -> List[MemoryEntity]:
        return self.find(key=key)
