"""prompt_repository.py — Prompt repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class PromptEntity(BaseEntity):
    __slots__ = ("name", "template", "version", "performance_score")

    def __init__(self, name: str, template: str = "") -> None:
        super().__init__()
        self.name = name
        self.template = template
        self.version: int = 1
        self.performance_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"name": self.name, "version": self.version,
                      "score": self.performance_score})
        return base


class PromptRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("prompt")

    def find_by_name(self, name: str) -> List[PromptEntity]:
        return self.find(name=name)

    def find_best(self, limit: int = 10) -> List[PromptEntity]:
        sorted_entities = sorted(self._store.values(),
                                  key=lambda e: e.performance_score, reverse=True)
        return sorted_entities[:limit]
