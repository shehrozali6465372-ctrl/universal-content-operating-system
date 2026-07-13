"""
Trend Entry Model
Layer 2: Research Engine — Module 1

Metadata model for a discovered trend.
"""

from datetime import datetime, timezone
from typing import List, Optional


class TrendEntry:
    """A single discovered trend with scoring and metadata."""

    __slots__ = (
        "trend_id", "keyword", "category", "source",
        "virality_score", "relevance_score", "freshness_score",
        "composite_score", "volume", "direction",
        "related_keywords", "discovered_at", "expires_at",
        "description", "tags",
    )

    DIRECTIONS = ["rising", "stable", "declining"]

    def __init__(
        self,
        keyword: str,
        category: str = "general",
        source: str = "unknown",
        virality_score: float = 0.0,
        relevance_score: float = 0.0,
        freshness_score: float = 0.0,
        volume: int = 0,
        direction: str = "rising",
        related_keywords: Optional[List[str]] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        expires_in_hours: int = 72,
    ):
        self.trend_id = f"{keyword.lower().replace(' ', '_')}_{source}"
        self.keyword = keyword
        self.category = category
        self.source = source
        self.virality_score = max(0.0, min(10.0, virality_score))
        self.relevance_score = max(0.0, min(10.0, relevance_score))
        self.freshness_score = max(0.0, min(10.0, freshness_score))
        self.volume = volume
        self.direction = direction if direction in self.DIRECTIONS else "stable"
        self.related_keywords = related_keywords or []
        self.description = description
        self.tags = tags or []
        self.discovered_at = datetime.now(timezone.utc).isoformat()
        self.expires_at = datetime(
            year=datetime.now(timezone.utc).year,
            month=datetime.now(timezone.utc).month,
            day=datetime.now(timezone.utc).day,
            hour=datetime.now(timezone.utc).hour,
            minute=datetime.now(timezone.utc).minute,
            second=datetime.now(timezone.utc).second,
        )

        from datetime import timedelta
        self.expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        ).isoformat()

        # Composite score: weighted average
        self.composite_score = round(
            (virality_score * 0.4 + relevance_score * 0.35 + freshness_score * 0.25),
            2,
        )

    def is_expired(self) -> bool:
        """Check if trend has expired."""
        return datetime.now(timezone.utc) > datetime.fromisoformat(self.expires_at)

    def to_dict(self) -> dict:
        return {
            "trend_id": self.trend_id,
            "keyword": self.keyword,
            "category": self.category,
            "source": self.source,
            "virality_score": self.virality_score,
            "relevance_score": self.relevance_score,
            "freshness_score": self.freshness_score,
            "composite_score": self.composite_score,
            "volume": self.volume,
            "direction": self.direction,
            "related_keywords": self.related_keywords,
            "description": self.description,
            "tags": self.tags,
            "discovered_at": self.discovered_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrendEntry":
        entry = cls(
            keyword=data["keyword"],
            category=data.get("category", "general"),
            source=data.get("source", "unknown"),
            virality_score=data.get("virality_score", 0.0),
            relevance_score=data.get("relevance_score", 0.0),
            freshness_score=data.get("freshness_score", 0.0),
            volume=data.get("volume", 0),
            direction=data.get("direction", "rising"),
            related_keywords=data.get("related_keywords", []),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )
        entry.trend_id = data.get("trend_id", entry.trend_id)
        entry.discovered_at = data.get("discovered_at", entry.discovered_at)
        entry.expires_at = data.get("expires_at", entry.expires_at)
        return entry
