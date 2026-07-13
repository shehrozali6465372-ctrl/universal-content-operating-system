"""
Memory Search Module
Layer 1: Core System — Module 5

Search engine for memory entries.
Supports keyword search, level filtering, tag filtering.
Designed to be swappable with vector search later.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    """Single search result."""
    id: int
    level: str
    category: str
    key: str
    value: str
    tags: List[str] = field(default_factory=list)
    relevance_score: float = 1.0


@dataclass
class SearchQuery:
    """Search query definition."""
    keyword: str = ""
    levels: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    category: str = ""
    limit: int = 20


class MemorySearchEngine:
    """
    Search engine for memory entries.
    Currently uses keyword matching.
    Can be extended with vector search (ChromaDB/FAISS) later.
    """

    def __init__(self):
        self._backend = "keyword"  # Future: "vector"

    def search(
        self,
        entries: List[Dict[str, Any]],
        query: SearchQuery,
    ) -> List[SearchResult]:
        """Search memory entries matching query."""
        results = []
        for entry in entries:
            score = self._score_entry(entry, query)
            if score > 0:
                results.append(SearchResult(
                    id=entry.get("id", 0),
                    level=entry.get("level", ""),
                    category=entry.get("category", ""),
                    key=entry.get("key", ""),
                    value=entry.get("value", ""),
                    tags=entry.get("tags", "").split(",") if entry.get("tags") else [],
                    relevance_score=score,
                ))

        # Sort by relevance
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:query.limit]

    def _score_entry(self, entry: Dict, query: SearchQuery) -> float:
        """Score an entry against a query. Returns 0 if not relevant."""
        score = 0.0

        # Level filter
        if query.levels and entry.get("level") not in query.levels:
            return 0.0

        # Category filter
        if query.category and entry.get("category") != query.category:
            return 0.0

        # Tag filter
        if query.tags:
            entry_tags = set(entry.get("tags", "").split(","))
            if not any(t in entry_tags for t in query.tags):
                return 0.0

        # Keyword match (simple text search)
        if query.keyword:
            keyword_lower = query.keyword.lower()
            key_match = keyword_lower in entry.get("key", "").lower()
            value_match = keyword_lower in entry.get("value", "").lower()
            category_match = keyword_lower in entry.get("category", "").lower()

            if key_match:
                score += 3.0
            if value_match:
                score += 2.0
            if category_match:
                score += 1.0

            if not (key_match or value_match or category_match):
                return 0.0
        else:
            score = 1.0  # No keyword = match all

        # Boost for importance
        importance = entry.get("importance", 0.5)
        score *= (0.5 + importance)

        return score

    def find_by_key(self, entries: List[Dict], key: str) -> Optional[Dict]:
        """Find exact key match."""
        for entry in entries:
            if entry.get("key") == key:
                return entry
        return None

    def find_by_category(self, entries: List[Dict], category: str) -> List[Dict]:
        """Find all entries in a category."""
        return [e for e in entries if e.get("category") == category]

    def find_by_tags(self, entries: List[Dict], tags: List[str]) -> List[Dict]:
        """Find entries matching any of the given tags."""
        results = []
        for entry in entries:
            entry_tags = set(entry.get("tags", "").split(","))
            if any(t in entry_tags for t in tags):
                results.append(entry)
        return results
