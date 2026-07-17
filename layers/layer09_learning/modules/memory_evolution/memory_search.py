"""Memory Search — Efficient search across memory entries."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class SearchResult:
    """A single search result."""

    __slots__ = ("entry_id", "relevance_score", "match_type", "data")

    def __init__(self, entry_id: str = "", relevance_score: float = 0.0) -> None:
        self.entry_id = entry_id
        self.relevance_score = relevance_score
        self.match_type: str = ""
        self.data: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "relevance_score": round(self.relevance_score, 3),
            "match_type": self.match_type,
        }


class MemorySearch:
    """Search memory entries by multiple criteria with relevance scoring."""

    def __init__(self) -> None:
        self._last_results: List[SearchResult] = []

    def search(self, entries: List[Dict[str, Any]], query: str = "",
               tags: Optional[List[str]] = None,
               category: str = "",
               min_score: float = 0.0,
               limit: int = 50) -> List[SearchResult]:
        results: List[SearchResult] = []
        for entry in entries:
            score = 0.0
            match_type = "exact"
            eid = entry.get("entry_id", "")
            if query:
                desc = entry.get("description", "").lower()
                if query.lower() in desc:
                    score += 0.8
                elif any(w in desc for w in query.lower().split()):
                    score += 0.4
                    match_type = "partial"
                else:
                    continue
            if tags:
                entry_tags = entry.get("tags", [])
                overlap = len(set(tags) & set(entry_tags))
                if overlap > 0:
                    score += min(0.5, overlap / len(tags))
                elif not query:
                    continue
            if category:
                if entry.get("category", "") == category:
                    score += 0.3
                elif not query and not tags:
                    continue
            entry_score = entry.get("score", 0.5)
            score += entry_score * 0.2
            if score >= min_score:
                sr = SearchResult(eid, score)
                sr.match_type = match_type
                sr.data = entry
                results.append(sr)
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        self._last_results = results[:limit]
        return list(self._last_results)

    def get_last_results(self) -> List[SearchResult]:
        return list(self._last_results)
