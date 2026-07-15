"""Memory Searcher — Search memories by various criteria."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class SearchResult:
    """A search result with relevance scoring."""
    __slots__ = ("entry", "relevance", "match_type")

    def __init__(self, entry: Any = None, relevance: float = 0.0, match_type: str = "") -> None:
        self.entry = entry
        self.relevance = relevance
        self.match_type = match_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relevance": round(self.relevance, 3),
            "match_type": self.match_type,
        }


class MemorySearcher:
    """Searches across multiple memory stores."""

    def __init__(self) -> None:
        self._stores: Dict[str, Any] = {}

    def register_store(self, name: str, store: Any) -> None:
        """Register a memory store for searching."""
        self._stores[name] = store

    def search(self, query: str, stores: Optional[List[str]] = None,
               limit: int = 10) -> List[SearchResult]:
        """Search across registered stores."""
        results: List[SearchResult] = []
        target_stores = stores or list(self._stores.keys())

        for store_name in target_stores:
            store = self._stores.get(store_name)
            if store is None:
                continue
            if hasattr(store, "search"):
                items = store.search(query)
                for item in items:
                    rel = self._calculate_relevance(query, item)
                    results.append(SearchResult(entry=item, relevance=rel, match_type=store_name))

        results.sort(key=lambda r: r.relevance, reverse=True)
        return results[:limit]

    def search_by_tag(self, tag: str, stores: Optional[List[str]] = None) -> List[SearchResult]:
        """Search by tag across stores."""
        results: List[SearchResult] = []
        target_stores = stores or list(self._stores.keys())

        for store_name in target_stores:
            store = self._stores.get(store_name)
            if store is None:
                continue
            if hasattr(store, "get_by_tag"):
                items = store.get_by_tag(tag)
                for item in items:
                    results.append(SearchResult(entry=item, relevance=0.8, match_type=store_name))
        return results

    def search_by_confidence(self, min_confidence: float = 0.7,
                             stores: Optional[List[str]] = None) -> List[SearchResult]:
        """Search for high-confidence entries."""
        results: List[SearchResult] = []
        target_stores = stores or list(self._stores.keys())

        for store_name in target_stores:
            store = self._stores.get(store_name)
            if store is None:
                continue
            if hasattr(store, "get_by_category"):
                for entry in store.get_by_category(""):
                    if hasattr(entry, "confidence") and entry.confidence >= min_confidence:
                        results.append(SearchResult(entry=entry, relevance=entry.confidence, match_type=store_name))
        return results

    def _calculate_relevance(self, query: str, item: Any) -> float:
        q = query.lower()
        score = 0.5
        if hasattr(item, "topic") and q in str(getattr(item, "topic", "")).lower():
            score += 0.3
        if hasattr(item, "tags") and q in " ".join(getattr(item, "tags", [])).lower():
            score += 0.2
        return min(score, 1.0)

    @property
    def store_count(self) -> int:
        return len(self._stores)
