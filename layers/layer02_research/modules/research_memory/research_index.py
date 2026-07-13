"""
Research Index
Layer 2: Research Engine — Module 7

Indexing system for research entries:
- Full-text indexing
- Category-based indexing
- Tag-based indexing
- Source-based indexing
- Time-based indexing
- Relevance scoring
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set


class ResearchEntry:
    """A single indexed research entry."""

    __slots__ = (
        "entry_id", "title", "content", "summary",
        "category", "tags", "source", "source_url",
        "keywords", "entities",
        "credibility_score", "relevance_score", "freshness_score",
        "composite_score", "access_count",
        "created_at", "last_accessed", "expires_at",
        "metadata",
    )

    def __init__(
        self,
        entry_id: str,
        title: str = "",
        content: str = "",
        summary: str = "",
        category: str = "general",
        tags: Optional[List[str]] = None,
        source: str = "",
        source_url: str = "",
        keywords: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        credibility_score: float = 0.5,
        relevance_score: float = 0.5,
        freshness_score: float = 0.5,
        metadata: Optional[Dict] = None,
    ):
        self.entry_id = entry_id
        self.title = title
        self.content = content
        self.summary = summary or content[:200]
        self.category = category
        self.tags = tags or []
        self.source = source
        self.source_url = source_url
        self.keywords = keywords or []
        self.entities = entities or []
        self.credibility_score = max(0.0, min(10.0, credibility_score))
        self.relevance_score = max(0.0, min(10.0, relevance_score))
        self.freshness_score = max(0.0, min(10.0, freshness_score))
        self.composite_score = round(
            (self.credibility_score * 0.3 + self.relevance_score * 0.4 + self.freshness_score * 0.3), 2
        )
        self.access_count = 0
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_accessed = self.created_at
        self.expires_at = ""
        self.metadata = metadata or {}

    def touch(self):
        """Record an access."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc).isoformat()

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            return datetime.now(timezone.utc) > datetime.fromisoformat(self.expires_at)
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id, "title": self.title,
            "content": self.content, "summary": self.summary,
            "category": self.category, "tags": self.tags,
            "source": self.source, "source_url": self.source_url,
            "keywords": self.keywords, "entities": self.entities,
            "credibility_score": self.credibility_score,
            "relevance_score": self.relevance_score,
            "freshness_score": self.freshness_score,
            "composite_score": self.composite_score,
            "access_count": self.access_count,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchEntry":
        e = cls(
            entry_id=data.get("entry_id", ""),
            title=data.get("title", ""), content=data.get("content", ""),
            summary=data.get("summary", ""),
            category=data.get("category", "general"),
            tags=data.get("tags", []), source=data.get("source", ""),
            source_url=data.get("source_url", ""),
            keywords=data.get("keywords", []),
            entities=data.get("entities", []),
            credibility_score=data.get("credibility_score", 0.5),
            relevance_score=data.get("relevance_score", 0.5),
            freshness_score=data.get("freshness_score", 0.5),
            metadata=data.get("metadata", {}),
        )
        e.access_count = data.get("access_count", 0)
        e.created_at = data.get("created_at", e.created_at)
        e.last_accessed = data.get("last_accessed", e.last_accessed)
        e.expires_at = data.get("expires_at", "")
        e.composite_score = data.get("composite_score", e.composite_score)
        return e


class ResearchIndex:
    """Full-text and faceted index for research entries."""

    def __init__(self):
        self._entries: Dict[str, ResearchEntry] = {}
        self._category_index: Dict[str, Set[str]] = defaultdict(set)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
        self._source_index: Dict[str, Set[str]] = defaultdict(set)
        self._keyword_index: Dict[str, Set[str]] = defaultdict(set)

    def add(self, entry: ResearchEntry):
        """Add an entry to the index."""
        self._entries[entry.entry_id] = entry
        self._category_index[entry.category].add(entry.entry_id)
        for tag in entry.tags:
            self._tag_index[tag.lower()].add(entry.entry_id)
        if entry.source:
            self._source_index[entry.source.lower()].add(entry.entry_id)
        for kw in entry.keywords:
            self._keyword_index[kw.lower()].add(entry.entry_id)

    def get(self, entry_id: str) -> Optional[ResearchEntry]:
        entry = self._entries.get(entry_id)
        if entry:
            entry.touch()
        return entry

    def remove(self, entry_id: str) -> bool:
        if entry_id not in self._entries:
            return False
        entry = self._entries.pop(entry_id)
        self._category_index[entry.category].discard(entry_id)
        for tag in entry.tags:
            self._tag_index[tag.lower()].discard(entry_id)
        if entry.source:
            self._source_index[entry.source.lower()].discard(entry_id)
        for kw in entry.keywords:
            self._keyword_index[kw.lower()].discard(entry_id)
        return True

    def search_text(self, query: str, max_results: int = 20) -> List[ResearchEntry]:
        """Full-text search across title, content, keywords."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        scores: Dict[str, float] = {}

        for eid, entry in self._entries.items():
            score = 0.0
            if query_lower in entry.title.lower():
                score += 3.0
            if query_lower in entry.summary.lower():
                score += 2.0
            if query_lower in entry.content.lower():
                score += 1.0
            # Keyword word overlap
            entry_words = set(k.lower() for k in entry.keywords)
            overlap = len(query_words & entry_words)
            score += overlap * 0.5
            if score > 0:
                scores[eid] = score + entry.composite_score * 0.1

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [self._entries[eid] for eid, _ in ranked[:max_results]]

    def search_by_category(self, category: str) -> List[ResearchEntry]:
        eids = self._category_index.get(category.lower(), set())
        return [self._entries[eid] for eid in eids if eid in self._entries]

    def search_by_tag(self, tag: str) -> List[ResearchEntry]:
        eids = self._tag_index.get(tag.lower(), set())
        return [self._entries[eid] for eid in eids if eid in self._entries]

    def search_by_source(self, source: str) -> List[ResearchEntry]:
        eids = self._source_index.get(source.lower(), set())
        return [self._entries[eid] for eid in eids if eid in self._entries]

    def search_by_keyword(self, keyword: str) -> List[ResearchEntry]:
        eids = self._keyword_index.get(keyword.lower(), set())
        return [self._entries[eid] for eid in eids if eid in self._entries]

    def get_top_entries(self, count: int = 10) -> List[ResearchEntry]:
        return sorted(self._entries.values(), key=lambda e: e.composite_score, reverse=True)[:count]

    def get_recent(self, count: int = 10) -> List[ResearchEntry]:
        return sorted(self._entries.values(), key=lambda e: e.created_at, reverse=True)[:count]

    def get_most_accessed(self, count: int = 10) -> List[ResearchEntry]:
        return sorted(self._entries.values(), key=lambda e: e.access_count, reverse=True)[:count]

    def size(self) -> int:
        return len(self._entries)

    def list_all(self) -> List[ResearchEntry]:
        return list(self._entries.values())

    def stats(self) -> dict:
        categories = set(e.category for e in self._entries.values())
        sources = set(e.source for e in self._entries.values() if e.source)
        return {
            "total_entries": len(self._entries),
            "categories": len(categories),
            "sources": len(sources),
            "avg_composite_score": round(
                sum(e.composite_score for e in self._entries.values()) / max(len(self._entries), 1), 2
            ),
        }
