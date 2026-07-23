"""VectorMemory — vector-based similarity search for memories."""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from .models import MemoryEntry, MemoryType


class VectorMemory:
    """Vector-based similarity search for memories using cosine similarity."""

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions
        self._entries: List[MemoryEntry] = []
        self._max_entries = 2000

    def store(self, content: str, embedding: Optional[List[float]] = None,
              tags: Optional[List[str]] = None, importance: float = 0.5) -> MemoryEntry:
        if embedding is None:
            embedding = self._generate_embedding(content)
        entry = MemoryEntry(
            content=content, memory_type=MemoryType.LONG_TERM,
            embedding=embedding, tags=tags or [], importance=importance,
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.sort(key=lambda e: e.importance)
            self._entries.pop(0)
        return entry

    def similarity_search(self, query: str, query_embedding: Optional[List[float]] = None,
                          top_k: int = 5) -> List[Tuple[MemoryEntry, float]]:
        if query_embedding is None:
            query_embedding = self._generate_embedding(query)
        scored = []
        for entry in self._entries:
            if entry.embedding:
                sim = self._cosine_similarity(query_embedding, entry.embedding)
                scored.append((entry, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def find_similar(self, entry_id: str, top_k: int = 5) -> List[Tuple[MemoryEntry, float]]:
        target = None
        for e in self._entries:
            if e.entry_id == entry_id:
                target = e
                break
        if not target or not target.embedding:
            return []
        scored = []
        for e in self._entries:
            if e.entry_id != entry_id and e.embedding:
                sim = self._cosine_similarity(target.embedding, e.embedding)
                scored.append((e, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def delete(self, entry_id: str) -> bool:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.entry_id != entry_id]
        return len(self._entries) < before

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    @staticmethod
    def _generate_embedding(text: str) -> List[float]:
        """Generate a simple deterministic embedding from text (for simulation)."""
        import hashlib
        h = hashlib.sha256(text.encode()).hexdigest()
        embedding = []
        for i in range(128):
            idx = i % len(h)
            val = (ord(h[idx]) - 127.5) / 127.5
            embedding.append(val)
        norm = math.sqrt(sum(v * v for v in embedding))
        if norm > 0:
            embedding = [v / norm for v in embedding]
        return embedding

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))
