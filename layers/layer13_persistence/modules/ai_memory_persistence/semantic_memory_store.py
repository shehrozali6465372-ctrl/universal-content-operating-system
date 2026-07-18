"""semantic_memory_store.py — Semantic memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class SemanticMemoryStore(BaseMemoryStore):
    """Stores semantic knowledge and facts."""

    def __init__(self, max_entries: int = 10000) -> None:
        super().__init__("semantic", max_entries)
        self._embeddings: Dict[str, List[float]] = {}

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "semantic")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def store_with_embedding(self, key: str, value: Any, embedding: List[float],
                              metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = self.store(key, value, metadata)
        self._embeddings[key] = embedding
        return entry

    def search_by_similarity(self, query_embedding: List[float],
                              top_k: int = 10) -> List[MemoryEntry]:
        scored = []
        for key, emb in self._embeddings.items():
            score = self._cosine(query_embedding, emb)
            entry = self._store.get(key)
            if entry:
                scored.append((entry, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:top_k]]

    def _cosine(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        return dot / (na * nb) if na > 0 and nb > 0 else 0.0

    def get_embedding(self, key: str) -> Optional[List[float]]:
        return self._embeddings.get(key)

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["with_embeddings"] = len(self._embeddings)
        return base
