"""vector_store.py — Core vector storage."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Tuple


class VectorRecord:
    """A stored vector record."""
    __slots__ = ("record_id", "vector", "metadata", "created_at")
    _counter = 0

    def __init__(self, vector: List[float], metadata: Dict[str, Any] = None) -> None:
        VectorRecord._counter += 1
        self.record_id: int = VectorRecord._counter
        self.vector = vector
        self.metadata = metadata or {}
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.record_id, "dimensions": len(self.vector),
                "metadata": dict(self.metadata)}


class VectorStore:
    """In-memory vector store with similarity search."""

    def __init__(self, dimensions: int = 1536) -> None:
        self._dimensions = dimensions
        self._records: Dict[int, VectorRecord] = {}

    def upsert(self, vector: List[float], metadata: Dict[str, Any] = None,
               record_id: Optional[int] = None) -> VectorRecord:
        if record_id and record_id in self._records:
            self._records[record_id].vector = vector
            if metadata:
                self._records[record_id].metadata = metadata
            return self._records[record_id]
        record = VectorRecord(vector, metadata)
        self._records[record.record_id] = record
        return record

    def search(self, query: List[float], top_k: int = 10,
               filter_metadata: Dict[str, Any] = None) -> List[Tuple[VectorRecord, float]]:
        results: List[Tuple[VectorRecord, float]] = []
        for record in self._records.values():
            if filter_metadata:
                match = all(record.metadata.get(k) == v for k, v in filter_metadata.items())
                if not match:
                    continue
            score = self._cosine_similarity(query, record.vector)
            results.append((record, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def delete(self, record_id: int) -> bool:
        return self._records.pop(record_id, None) is not None

    def get(self, record_id: int) -> Optional[VectorRecord]:
        return self._records.get(record_id)

    def count(self) -> int:
        return len(self._records)

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b) or len(a) == 0:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def stats(self) -> Dict[str, Any]:
        return {"records": len(self._records), "dimensions": self._dimensions}
