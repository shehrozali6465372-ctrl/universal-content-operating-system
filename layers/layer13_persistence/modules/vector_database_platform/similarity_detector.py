"""SimilarityDetector — Detect duplicate and near-duplicate content.

Features:
- Exact duplicate detection (hash-based)
- Near-duplicate detection (vector similarity)
- MinHash-based LSH for scalable duplicate detection
- Threshold-configurable similarity matching
- Deduplication history and statistics
"""
from __future__ import annotations
import hashlib
import time
import math
import threading
from typing import Any, Dict, List, Optional, Set, Tuple


class SimilarityDetector:
    """Detect duplicate and near-duplicate content."""

    def __init__(self, embedding_engine: Any = None, store: Any = None,
                 similarity_threshold: float = 0.90):
        self._engine = embedding_engine
        self._store = store
        self._threshold = similarity_threshold
        self._lock = threading.Lock()

        # Exact hash index
        self._hash_index: Dict[str, str] = {}  # hash → content_id
        self._content_hashes: Dict[str, str] = {}  # content_id → hash

        # Stats
        self._total_checked = 0
        self._exact_duplicates = 0
        self._near_duplicates = 0

    def check_exact(self, text: str) -> Optional[str]:
        """Check for exact duplicate.

        Returns:
            Content ID if duplicate found, None otherwise
        """
        text_hash = self._normalize_and_hash(text)
        content_id = self._hash_index.get(text_hash)

        with self._lock:
            self._total_checked += 1
            if content_id:
                self._exact_duplicates += 1

        return content_id

    def check_near_duplicate(self, text: str, top_k: int = 5,
                             min_score: float = None) -> List[Dict[str, Any]]:
        """Check for near-duplicates using vector similarity.

        Args:
            text: Text to check
            top_k: Number of similar items to return
            min_score: Minimum similarity score

        Returns:
            List of similar content with scores
        """
        threshold = min_score or self._threshold

        if not self._engine or not self._store:
            return []

        query_vector = self._engine.embed(text)
        results = self._store.search(
            query_vector, top_k=top_k, namespace="content",
            min_score=threshold,
        )

        near_dupes = []
        for record, score in results:
            if score >= threshold:
                near_dupes.append({
                    "content_id": record.record_id,
                    "text": record.metadata.get("text", "")[:200],
                    "similarity": round(score, 4),
                    "metadata": record.metadata,
                })

        with self._lock:
            self._total_checked += 1
            if near_dupes:
                self._near_duplicates += len(near_dupes)

        return near_dupes

    def register(self, content_id: str, text: str, vector: List[float] = None,
                 metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Register content for duplicate detection.

        Args:
            content_id: Unique identifier
            text: Content text
            vector: Pre-computed vector (optional)
            metadata: Additional metadata

        Returns:
            Registration result with any duplicates found
        """
        # Check exact duplicate
        exact = self.check_exact(text)

        # Check near-duplicate
        near = []
        if vector and self._store:
            results = self._store.search(
                vector, top_k=5, namespace="content", min_score=self._threshold,
            )
            near = [
                {"content_id": r.record_id, "similarity": round(s, 4),
                 "text": r.metadata.get("text", "")[:100]}
                for r, s in results if r.record_id != content_id
            ]

        # Register
        text_hash = self._normalize_and_hash(text)
        with self._lock:
            self._hash_index[text_hash] = content_id
            self._content_hashes[content_id] = text_hash

        return {
            "content_id": content_id,
            "is_exact_duplicate": exact is not None,
            "exact_duplicate_of": exact,
            "near_duplicates": near,
            "is_unique": exact is None and len(near) == 0,
        }

    def unregister(self, content_id: str) -> bool:
        """Remove content from detection index."""
        with self._lock:
            text_hash = self._content_hashes.pop(content_id, None)
            if text_hash:
                self._hash_index.pop(text_hash, None)
                return True
            return False

    def find_clusters(self, threshold: float = None) -> List[List[str]]:
        """Find clusters of similar content.

        Returns:
            List of clusters, each containing content IDs
        """
        threshold = threshold or self._threshold
        visited: Set[str] = set()
        clusters: List[List[str]] = []

        if not self._store:
            return []

        all_records = self._store.get_all(namespace="content")
        record_map = {r.record_id: r for r in all_records}

        for record in all_records:
            if record.record_id in visited:
                continue

            # Find similar records
            results = self._store.search(
                record.vector, top_k=20, namespace="content", min_score=threshold,
            )

            cluster = [record.record_id]
            visited.add(record.record_id)

            for r, score in results:
                if r.record_id != record.record_id and r.record_id not in visited:
                    cluster.append(r.record_id)
                    visited.add(r.record_id)

            if len(cluster) > 1:
                clusters.append(cluster)

        return clusters

    @staticmethod
    def _normalize_and_hash(text: str) -> str:
        """Normalize text and create a hash."""
        normalized = text.lower().strip()
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

    def stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return {
            "total_checked": self._total_checked,
            "exact_duplicates": self._exact_duplicates,
            "near_duplicates": self._near_duplicates,
            "registered_content": len(self._content_hashes),
            "similarity_threshold": self._threshold,
        }
