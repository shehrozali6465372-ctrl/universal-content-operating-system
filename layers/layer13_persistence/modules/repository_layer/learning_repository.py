"""learning_repository.py — Learning repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class LearningEntity(BaseEntity):
    __slots__ = ("lesson_type", "description", "impact", "confidence", "applied")

    def __init__(self, lesson_type: str, description: str, impact: str = "medium") -> None:
        super().__init__()
        self.lesson_type = lesson_type
        self.description = description
        self.impact = impact
        self.confidence: float = 0.5
        self.applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"type": self.lesson_type, "impact": self.impact,
                      "applied": self.applied})
        return base


class LearningRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("learning")

    def find_by_type(self, lesson_type: str) -> List[LearningEntity]:
        return self.find(lesson_type=lesson_type)

    def find_applied(self) -> List[LearningEntity]:
        return self.find(applied=True)

    def find_unapplied(self) -> List[LearningEntity]:
        return [e for e in self._store.values() if not e.applied]
