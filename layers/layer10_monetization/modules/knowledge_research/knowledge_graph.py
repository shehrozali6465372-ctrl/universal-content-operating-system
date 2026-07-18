"""KnowledgeGraph — Universal AI knowledge storage."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_KG_COUNTER = itertools.count(1)


class KnowledgeEntity:
    """An entity in the knowledge graph."""

    __slots__ = ("entity_id", "name", "entity_type", "attributes",
                 "relationships", "sources", "confidence", "last_updated")

    def __init__(self, name: str = "", entity_type: str = "") -> None:
        self.entity_id: str = f"ke_{next(_KG_COUNTER)}"
        self.name = name
        self.entity_type = entity_type
        self.attributes: Dict[str, Any] = {}
        self.relationships: List[Dict[str, str]] = []
        self.sources: List[str] = []
        self.confidence: float = 0.5
        self.last_updated: float = time.time()

    def add_relationship(self, target: str, relation: str) -> None:
        self.relationships.append({"target": target, "relation": relation})

    def to_dict(self) -> Dict[str, Any]:
        return {"entity_id": self.entity_id, "name": self.name,
                "type": self.entity_type, "confidence": round(self.confidence, 3),
                "relationships": len(self.relationships)}


class KnowledgeGraph:
    """Store topics, keywords, entities, relationships, and sources."""

    def __init__(self) -> None:
        self._entities: List[KnowledgeEntity] = []
        self._entity_index: Dict[str, KnowledgeEntity] = {}

    def add_entity(self, name: str, entity_type: str = "topic") -> KnowledgeEntity:
        entity = KnowledgeEntity(name, entity_type)
        self._entities.append(entity)
        self._entity_index[name.lower()] = entity
        return entity

    def get_entity(self, name: str) -> Optional[KnowledgeEntity]:
        return self._entity_index.get(name.lower())

    def add_relationship(self, source: str, target: str, relation: str) -> bool:
        src = self.get_entity(source)
        tgt = self.get_entity(target)
        if src and tgt:
            src.add_relationship(tgt.entity_id, relation)
            return True
        return False

    def search(self, query: str = "", entity_type: str = "",
               min_confidence: float = 0.0) -> List[KnowledgeEntity]:
        results = self._entities
        if query:
            results = [e for e in results if query.lower() in e.name.lower()]
        if entity_type:
            results = [e for e in results if e.entity_type == entity_type]
        if min_confidence > 0:
            results = [e for e in results if e.confidence >= min_confidence]
        return results

    def exists(self, name: str) -> bool:
        return name.lower() in self._entity_index

    def get_stats(self) -> Dict[str, Any]:
        types = {}
        for e in self._entities:
            types[e.entity_type] = types.get(e.entity_type, 0) + 1
        return {"total_entities": len(self._entities), "by_type": types}
