"""SemanticSearch — Advanced semantic search with hybrid ranking.

Features:
- Pure vector similarity search
- Metadata-filtered search
- Hybrid search (vector + keyword)
- Multi-query fusion (RRF — Reciprocal Rank Fusion)
- Search result ranking with configurable weights
- Search history and analytics
"""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple


class SemanticSearch:
    """Advanced semantic search engine."""

    def __init__(self, store: Any, embedding_engine: Any = None):
        self._store = store
        self._engine = embedding_engine
        self._lock = threading.Lock()

        # Search history
        self._history: List[Dict[str, Any]] = []
        self._max_history = 1000

        # Stats
        self._total_searches = 0
        self._total_results = 0

    def search(self, query: str, top_k: int = 10, namespace: str = None,
               min_score: float = 0.0, metadata_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Semantic search using text query.

        Args:
            query: Natural language query
            top_k: Number of results
            namespace: Filter by namespace
            min_score: Minimum similarity score
            metadata_filter: Filter by metadata key-value pairs

        Returns:
            List of result dicts with record, score, and metadata
        """
        if not self._engine:
            raise ValueError("EmbeddingEngine not configured")

        start = time.time()
        query_vector = self._engine.embed(query)

        # Build filter function
        filter_fn = None
        if metadata_filter:
            def filter_fn(record):
                return all(record.metadata.get(k) == v for k, v in metadata_filter.items())

        # Search
        results = self._store.search(
            query_vector, top_k=top_k * 2,  # Over-fetch for reranking
            namespace=namespace, filter_fn=filter_fn, min_score=min_score,
        )

        # Rerank with text relevance boost
        reranked = []
        query_words = set(query.lower().split())
        for record, score in results:
            # Boost score if text contains query words
            text = record.metadata.get("text", "")
            text_lower = text.lower()
            word_overlap = sum(1 for w in query_words if w in text_lower)
            text_boost = min(0.1, word_overlap * 0.02)  # Max 10% boost
            final_score = min(1.0, score + text_boost)

            reranked.append({
                "record": record,
                "score": round(final_score, 4),
                "text": text[:500],
                "metadata": record.metadata,
                "record_id": record.record_id,
                "namespace": record.namespace,
            })

        reranked.sort(key=lambda x: x["score"], reverse=True)
        reranked = reranked[:top_k]

        elapsed_ms = (time.time() - start) * 1000

        # Track
        with self._lock:
            self._total_searches += 1
            self._total_results += len(reranked)
            self._history.append({
                "query": query[:200],
                "top_k": top_k,
                "results": len(reranked),
                "elapsed_ms": round(elapsed_ms, 1),
                "timestamp": time.time(),
            })
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        return reranked

    def multi_query_search(self, queries: List[str], top_k: int = 10,
                           namespace: str = None) -> List[Dict[str, Any]]:
        """Search with multiple queries and fuse results using RRF."""
        all_results: Dict[str, Dict[str, Any]] = {}
        rank_lists: List[List[str]] = []

        for query in queries:
            results = self.search(query, top_k=top_k * 2, namespace=namespace)
            ranked_ids = [r["record_id"] for r in results]
            rank_lists.append(ranked_ids)

            for r in results:
                all_results[r["record_id"]] = r

        # Reciprocal Rank Fusion
        k = 60  # RRF constant
        scores: Dict[str, float] = {}
        for rank_list in rank_lists:
            for rank, doc_id in enumerate(rank_list):
                if doc_id not in scores:
                    scores[doc_id] = 0.0
                scores[doc_id] += 1.0 / (k + rank + 1)

        # Sort by fused score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        fused_results = []
        for doc_id in sorted_ids[:top_k]:
            if doc_id in all_results:
                result = all_results[doc_id].copy()
                result["rrf_score"] = round(scores[doc_id], 4)
                fused_results.append(result)

        return fused_results

    def find_similar(self, record_id: str, top_k: int = 10,
                     namespace: str = None) -> List[Dict[str, Any]]:
        """Find records similar to a given record."""
        record = self._store.get(record_id)
        if not record:
            return []

        results = self._store.search(
            record.vector, top_k=top_k + 1,  # +1 to exclude self
            namespace=namespace,
        )

        similar = []
        for r, score in results:
            if r.record_id == record_id:
                continue  # Skip self
            similar.append({
                "record": r,
                "score": round(score, 4),
                "text": r.metadata.get("text", ""),
                "record_id": r.record_id,
            })

        return similar[:top_k]

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent search history."""
        with self._lock:
            return list(self._history[-limit:])

    def stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        with self._lock:
            return {
                "total_searches": self._total_searches,
                "total_results": self._total_results,
                "avg_results_per_search": round(
                    self._total_results / self._total_searches, 1
                ) if self._total_searches > 0 else 0,
                "history_size": len(self._history),
            }
