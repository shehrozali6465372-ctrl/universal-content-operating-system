"""SourceManager — Manage research sources."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_SM_COUNTER = itertools.count(1)


class ResearchSource:
    """A research source."""

    __slots__ = ("source_id", "name", "source_type", "url", "trust_score",
                 "priority", "rate_limit", "enabled")

    def __init__(self, name: str = "", source_type: str = "") -> None:
        self.source_id: str = f"src_{next(_SM_COUNTER)}"
        self.name = name
        self.source_type = source_type
        self.url: str = ""
        self.trust_score: float = 0.5
        self.priority: int = 1
        self.rate_limit: int = 100
        self.enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"source_id": self.source_id, "name": self.name,
                "type": self.source_type, "trust": round(self.trust_score, 3)}


class SourceManager:
    """Manage research sources with trust scores and rate limits."""

    def __init__(self) -> None:
        self._sources: List[ResearchSource] = []

    def add_source(self, name: str, source_type: str = "api",
                   trust_score: float = 0.5) -> ResearchSource:
        source = ResearchSource(name, source_type)
        source.trust_score = trust_score
        self._sources.append(source)
        return source

    def get_source(self, source_id: str) -> ResearchSource:
        for s in self._sources:
            if s.source_id == source_id:
                return s
        return None

    def get_by_type(self, source_type: str) -> List[ResearchSource]:
        return [s for s in self._sources if s.source_type == source_type]

    def get_trusted(self, min_trust: float = 0.5) -> List[ResearchSource]:
        return [s for s in self._sources if s.trust_score >= min_trust and s.enabled]

    def get_all(self) -> List[ResearchSource]:
        return list(self._sources)

    def get_stats(self) -> Dict[str, Any]:
        types = {}
        for s in self._sources:
            types[s.source_type] = types.get(s.source_type, 0) + 1
        return {"total": len(self._sources), "by_type": types}
