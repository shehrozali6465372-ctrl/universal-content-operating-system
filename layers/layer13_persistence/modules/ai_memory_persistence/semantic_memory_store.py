"""semantic_memory_store.py — Semantic memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.shared.vector_math import cosine_similarity
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

    def store_with_embedding(self, key: str, value: Any, embedding: List[float],
                              metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = self.store(key, value, metadata)
        self._embeddings[key] = embedding
        return entry

    def search_by_similarity(self, query_embedding: List[float],
                              top_k: int = 10) -> List[MemoryEntry]:
        scored = []
        for key, emb in self._embeddings.items():
            score = cosine_similarity(query_embedding, emb)
            entry = self._store.get(key)
            if entry:
                scored.append((entry, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:top_k]]

    def get_embedding(self, key: str) -> Optional[List[float]]:
        return self._embeddings.get(key)

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["with_embeddings"] = len(self._embeddings)
        return base
