"""research_repository.py — Research repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class ResearchEntity(BaseEntity):
    __slots__ = ("query", "results", "source", "confidence", "cached")

    def __init__(self, query: str, results: Any = None, source: str = "") -> None:
        super().__init__()
        self.query = query
        self.results = results or {}
        self.source = source
        self.confidence: float = 0.5
        self.cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"query": self.query, "source": self.source,
                      "confidence": self.confidence})
        return base


class ResearchRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("research")

    def find_by_source(self, source: str) -> List[ResearchEntity]:
        return self.find(source=source)

    def find_high_confidence(self, min_confidence: float = 0.7) -> List[ResearchEntity]:
        return [e for e in self._store.values() if e.confidence >= min_confidence]
