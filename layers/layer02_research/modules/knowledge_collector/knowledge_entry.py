"""
Knowledge Entry Model
Layer 2: Research Engine — Module 5

Data model for a collected knowledge document.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import random


class KnowledgeEntry:
    """A single collected knowledge document."""

    __slots__ = (
        "entry_id", "title", "source", "source_url", "published_at",
        "author", "language", "content", "summary",
        "keywords", "entities", "tags", "category",
        "credibility_score", "freshness_score", "relevance_score",
        "composite_score", "word_count",
        "is_duplicate", "duplicate_of",
        "content_hash", "metadata",
        "collected_at", "expires_at", "status",
    )

    STATUSES = ["active", "expired", "archived", "flagged", "promoted"]

    def __init__(
        self,
        title: str = "",
        source: str = "",
        source_url: str = "",
        published_at: str = "",
        author: str = "",
        language: str = "en",
        content: str = "",
        summary: str = "",
        keywords: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        category: str = "general",
        credibility_score: float = 0.5,
        freshness_score: float = 0.5,
        relevance_score: float = 0.5,
        metadata: Optional[Dict] = None,
        expires_in_hours: int = 720,
    ):
        self.entry_id = f"kb_{int(datetime.now(timezone.utc).timestamp())}_{random.randint(100000, 999999)}"
        self.title = title
        self.source = source
        self.source_url = source_url
        self.published_at = published_at
        self.author = author
        self.language = language
        self.content = content
        self.summary = summary
        self.keywords = keywords or []
        self.entities = entities or []
        self.tags = tags or []
        self.category = category
        self.credibility_score = self._clamp(credibility_score)
        self.freshness_score = self._clamp(freshness_score)
        self.relevance_score = self._clamp(relevance_score)
        self.word_count = len(content.split()) if content else 0
        self.is_duplicate = False
        self.duplicate_of = ""
        self.metadata = metadata or {}
        self.status = "active"

        # Composite score
        self.composite_score = round(
            (self.credibility_score * 0.35 +
             self.freshness_score * 0.25 +
             self.relevance_score * 0.40),
            2,
        )

        # Content hash for dedup
        self.content_hash = self._hash_content(title + content)

        # Timestamps
        self.collected_at = datetime.now(timezone.utc).isoformat()
        self.expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        ).isoformat()

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
        return max(low, min(high, value))

    @staticmethod
    def _hash_content(text: str) -> str:
        """Simple content hash for deduplication."""
        import hashlib
        normalized = text.lower().strip()[:1000]
        return hashlib.sha256(normalized.encode()).hexdigest()

    def is_expired(self) -> bool:
        try:
            return datetime.now(timezone.utc) > datetime.fromisoformat(self.expires_at)
        except (ValueError, TypeError):
            return True

    def is_trustworthy(self) -> bool:
        return self.credibility_score >= 0.6 and not self.is_duplicate

    def get_age_hours(self) -> float:
        """Hours since collection."""
        try:
            collected = datetime.fromisoformat(self.collected_at)
            delta = datetime.now(timezone.utc) - collected
            return round(delta.total_seconds() / 3600, 1)
        except (ValueError, TypeError):
            return 0.0

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id, "title": self.title,
            "source": self.source, "source_url": self.source_url,
            "published_at": self.published_at, "author": self.author,
            "language": self.language, "content": self.content,
            "summary": self.summary, "keywords": self.keywords,
            "entities": self.entities, "tags": self.tags,
            "category": self.category,
            "credibility_score": self.credibility_score,
            "freshness_score": self.freshness_score,
            "relevance_score": self.relevance_score,
            "composite_score": self.composite_score,
            "word_count": self.word_count,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
            "content_hash": self.content_hash,
            "metadata": self.metadata, "status": self.status,
            "collected_at": self.collected_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeEntry":
        e = cls(
            title=data.get("title", ""), source=data.get("source", ""),
            source_url=data.get("source_url", ""),
            published_at=data.get("published_at", ""),
            author=data.get("author", ""), language=data.get("language", "en"),
            content=data.get("content", ""), summary=data.get("summary", ""),
            keywords=data.get("keywords", []), entities=data.get("entities", []),
            tags=data.get("tags", []), category=data.get("category", "general"),
            credibility_score=data.get("credibility_score", 0.5),
            freshness_score=data.get("freshness_score", 0.5),
            relevance_score=data.get("relevance_score", 0.5),
            metadata=data.get("metadata", {}),
        )
        e.entry_id = data.get("entry_id", e.entry_id)
        e.is_duplicate = data.get("is_duplicate", False)
        e.duplicate_of = data.get("duplicate_of", "")
        e.content_hash = data.get("content_hash", e.content_hash)
        e.status = data.get("status", "active")
        e.collected_at = data.get("collected_at", e.collected_at)
        e.expires_at = data.get("expires_at", e.expires_at)
        e.composite_score = data.get("composite_score", e.composite_score)
        e.word_count = data.get("word_count", e.word_count)
        return e
