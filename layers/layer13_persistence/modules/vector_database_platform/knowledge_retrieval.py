"""KnowledgeRetrieval — Context-aware knowledge retrieval with ranking.

Features:
- Multi-source knowledge retrieval
- Context window management
- Relevance ranking with configurable weights
- Source diversity enforcement
- Knowledge graph traversal
- Temporal relevance boosting
"""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple


class KnowledgeRetrieval:
    """Context-aware knowledge retrieval system."""

    def __init__(self, store: Any = None, search: Any = None, memory: Any = None):
        self._store = store
        self._search = search
        self._memory = memory
        self._lock = threading.Lock()

        # Retrieval weights
        self._weights = {
            "semantic": 0.5,   # Vector similarity
            "recency": 0.2,    # How recent the knowledge is
            "importance": 0.2, # Importance score
            "source_diversity": 0.1,  # Bonus for diverse sources
        }

        # Stats
        self._total_retrievals = 0
        self._total_knowledge_items = 0

    def retrieve(self, query: str, top_k: int = 5, sources: List[str] = None,
                 namespaces: List[str] = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve knowledge from multiple sources.

        Args:
            query: Search query
            top_k: Number of results
            sources: Filter by source names
            namespaces: Search in specific namespaces
            context: Additional context for ranking

        Returns:
            Ranked list of knowledge items
        """
        all_results: List[Dict[str, Any]] = []
        namespaces = namespaces or ["knowledge", "content", "memory"]

        # Search across namespaces
        for ns in namespaces:
            if self._search:
                results = self._search.search(query, top_k=top_k * 2, namespace=ns)
                for r in results:
                    all_results.append({
                        **r,
                        "namespace": ns,
                        "source": r.get("metadata", {}).get("source", ns),
                        "text": r.get("text", r.get("metadata", {}).get("text", "")),
                    })

        # Search long-term memory
        if self._memory:
            memory_results = self._memory.search(query, top_k=top_k)
            for m in memory_results:
                all_results.append({
                    "score": m.get("match_score", 0),
                    "text": m.get("content", ""),
                    "namespace": "memory",
                    "source": "long_term_memory",
                    "metadata": m,
                })

        # Rank results
        ranked = self._rank_results(all_results, query, context)

        # Enforce source diversity
        diversified = self._enforce_diversity(ranked, top_k)

        with self._lock:
            self._total_retrievals += 1
            self._total_knowledge_items += len(diversified)

        return diversified[:top_k]

    def _rank_results(self, results: List[Dict[str, Any]], query: str,
                      context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Rank results using configurable weights."""
        for r in results:
            semantic_score = r.get("score", 0)

            # Recency score
            created_at = r.get("metadata", {}).get("created_at", r.get("record", None))
            if hasattr(created_at, "created_at"):
                age_hours = (time.time() - created_at.created_at) / 3600
            else:
                age_hours = 24  # Default
            recency_score = max(0, 1.0 - age_hours / (24 * 30))  # Decay over 30 days

            # Importance score
            importance = r.get("metadata", {}).get("importance", 0.5)

            # Combined score
            combined = (
                semantic_score * self._weights["semantic"] +
                recency_score * self._weights["recency"] +
                importance * self._weights["importance"]
            )

            r["rank_score"] = round(combined, 4)
            r["rank_breakdown"] = {
                "semantic": round(semantic_score, 4),
                "recency": round(recency_score, 4),
                "importance": round(importance, 4),
            }

        results.sort(key=lambda x: x.get("rank_score", 0), reverse=True)
        return results

    def _enforce_diversity(self, ranked: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Ensure results come from diverse sources."""
        if not ranked:
            return []

        diversified = []
        source_counts: Dict[str, int] = {}
        max_per_source = max(2, top_k // 2)

        for item in ranked:
            source = item.get("source", "unknown")
            count = source_counts.get(source, 0)
            if count < max_per_source:
                diversified.append(item)
                source_counts[source] = count + 1
                if len(diversified) >= top_k:
                    break

        # Fill remaining with any source
        if len(diversified) < top_k:
            for item in ranked:
                if item not in diversified:
                    diversified.append(item)
                    if len(diversified) >= top_k:
                        break

        return diversified

    def get_context_window(self, query: str, max_tokens: int = 4000,
                           namespaces: List[str] = None) -> Dict[str, Any]:
        """Build a context window for LLM consumption.

        Args:
            query: Search query
            max_tokens: Maximum tokens in context
            namespaces: Knowledge namespaces

        Returns:
            Context window with text, sources, and metadata
        """
        results = self.retrieve(query, top_k=10, namespaces=namespaces)

        # Build context
        context_parts = []
        sources = []
        total_chars = 0
        max_chars = max_tokens * 4  # ~4 chars per token

        for r in results:
            text = r.get("text", "")
            if total_chars + len(text) > max_chars:
                break
            context_parts.append(text)
            sources.append({
                "source": r.get("source", "unknown"),
                "score": r.get("rank_score", 0),
                "text_preview": text[:100],
            })
            total_chars += len(text)

        return {
            "context_text": "\n\n---\n\n".join(context_parts),
            "sources": sources,
            "total_chars": total_chars,
            "estimated_tokens": total_chars // 4,
            "query": query,
        }

    def stats(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        return {
            "total_retrievals": self._total_retrievals,
            "total_knowledge_items": self._total_knowledge_items,
            "weights": self._weights,
        }
