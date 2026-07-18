"""knowledge_memory_store.py — Knowledge memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class KnowledgeGraph:
    """Simple knowledge graph."""

    def __init__(self) -> None:
        self._entities: Dict[str, Dict[str, Any]] = {}
        self._relationships: List[Dict[str, str]] = []

    def add_entity(self, name: str, entity_type: str,
                   properties: Dict[str, Any] = None) -> None:
        self._entities[name] = {"type": entity_type, "properties": properties or {}}

    def add_relationship(self, source: str, target: str, relation: str) -> None:
        self._relationships.append({"source": source, "target": target, "relation": relation})

    def get_entity(self, name: str) -> Optional[Dict[str, Any]]:
        return self._entities.get(name)

    def get_relationships(self, entity: str) -> List[Dict[str, str]]:
        return [r for r in self._relationships if r["source"] == entity or r["target"] == entity]

    def entity_count(self) -> int:
        return len(self._entities)

    def relationship_count(self) -> int:
        return len(self._relationships)


class KnowledgeMemoryStore(BaseMemoryStore):
    """Stores knowledge and facts."""

    def __init__(self, max_entries: int = 10000) -> None:
        super().__init__("knowledge", max_entries)
        self._graph = KnowledgeGraph()

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "knowledge")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def get_graph(self) -> KnowledgeGraph:
        return self._graph

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["graph_entities"] = self._graph.entity_count()
        base["graph_relationships"] = self._graph.relationship_count()
        return base
