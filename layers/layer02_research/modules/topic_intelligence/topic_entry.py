"""
Topic Entry Model
Layer 2: Research Engine — Module 2

Metadata model for a Facebook topic with scoring and categorization.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


class TopicEntry:
    """A Facebook content topic with multi-dimensional scoring."""

    __slots__ = (
        "topic_id", "name", "niche", "category",
        "engagement_score", "audience_fit_score", "competition_score",
        "opportunity_score", "composite_score",
        "estimated_reach", "difficulty_level",
        "keywords", "hashtags", "related_topics",
        "source_trend_id", "confidence",
        "created_at", "updated_at", "expires_at",
        "status", "tags", "metadata",
    )

    NICHES = [
        "finance", "technology", "health", "lifestyle",
        "education", "entertainment", "business", "marketing",
        "ai", "crypto", "fitness", "cooking", "travel",
        "parenting", "motivation", "general",
    ]

    DIFFICULTY_LEVELS = ["easy", "medium", "hard", "very_hard"]

    STATUSES = ["active", "pending", "expired", "archived", "promoted"]

    def __init__(
        self,
        name: str,
        niche: str = "general",
        category: str = "general",
        engagement_score: float = 0.0,
        audience_fit_score: float = 0.0,
        competition_score: float = 0.0,
        estimated_reach: int = 0,
        difficulty_level: str = "medium",
        keywords: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        related_topics: Optional[List[str]] = None,
        source_trend_id: str = "",
        confidence: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        expires_in_hours: int = 168,
    ):
        self.topic_id = f"topic_{name.lower().replace(' ', '_')}_{int(datetime.now(timezone.utc).timestamp())}"
        self.name = name
        self.niche = niche if niche in self.NICHES else "general"
        self.category = category
        self.keywords = keywords or []
        self.hashtags = hashtags or []
        self.related_topics = related_topics or []
        self.source_trend_id = source_trend_id
        self.tags = tags or []
        self.metadata = metadata or {}

        # Scoring (0-10 scale)
        self.engagement_score = self._clamp(engagement_score)
        self.audience_fit_score = self._clamp(audience_fit_score)
        self.competition_score = self._clamp(competition_score)

        # Difficulty
        self.difficulty_level = difficulty_level if difficulty_level in self.DIFFICULTY_LEVELS else "medium"

        # Reach
        self.estimated_reach = max(0, estimated_reach)

        # Confidence
        self.confidence = max(0.0, min(1.0, confidence))

        # Opportunity score: high engagement + low competition = high opportunity
        # Scale: 0-10
        raw_opportunity = (
            (self.engagement_score * 0.4) +
            (self.audience_fit_score * 0.3) +
            ((10.0 - self.competition_score) * 0.3)
        )
        self.opportunity_score = round(self._clamp(raw_opportunity), 2)

        # Composite: weighted blend of all factors
        self.composite_score = round(
            (self.engagement_score * 0.35 +
             self.audience_fit_score * 0.25 +
             self.opportunity_score * 0.25 +
             self.confidence * 10.0 * 0.15),
            2,
        )

        # Status
        self.status = "active"

        # Timestamps
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        ).isoformat()

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
        return max(low, min(high, value))

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > datetime.fromisoformat(self.expires_at)

    def is_promotable(self) -> bool:
        return (
            self.status == "active"
            and not self.is_expired()
            and self.composite_score >= 7.0
            and self.confidence >= 0.6
        )

    def update_scores(
        self,
        engagement_score: Optional[float] = None,
        audience_fit_score: Optional[float] = None,
        competition_score: Optional[float] = None,
    ):
        """Recalculate scores after update."""
        if engagement_score is not None:
            self.engagement_score = self._clamp(engagement_score)
        if audience_fit_score is not None:
            self.audience_fit_score = self._clamp(audience_fit_score)
        if competition_score is not None:
            self.competition_score = self._clamp(competition_score)

        raw_opportunity = (
            (self.engagement_score * 0.4) +
            (self.audience_fit_score * 0.3) +
            ((10.0 - self.competition_score) * 0.3)
        )
        self.opportunity_score = round(self._clamp(raw_opportunity), 2)

        self.composite_score = round(
            (self.engagement_score * 0.35 +
             self.audience_fit_score * 0.25 +
             self.opportunity_score * 0.25 +
             self.confidence * 10.0 * 0.15),
            2,
        )
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "topic_id": self.topic_id,
            "name": self.name,
            "niche": self.niche,
            "category": self.category,
            "engagement_score": self.engagement_score,
            "audience_fit_score": self.audience_fit_score,
            "competition_score": self.competition_score,
            "opportunity_score": self.opportunity_score,
            "composite_score": self.composite_score,
            "estimated_reach": self.estimated_reach,
            "difficulty_level": self.difficulty_level,
            "keywords": self.keywords,
            "hashtags": self.hashtags,
            "related_topics": self.related_topics,
            "source_trend_id": self.source_trend_id,
            "confidence": self.confidence,
            "status": self.status,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TopicEntry":
        entry = cls(
            name=data["name"],
            niche=data.get("niche", "general"),
            category=data.get("category", "general"),
            engagement_score=data.get("engagement_score", 0.0),
            audience_fit_score=data.get("audience_fit_score", 0.0),
            competition_score=data.get("competition_score", 0.0),
            estimated_reach=data.get("estimated_reach", 0),
            difficulty_level=data.get("difficulty_level", "medium"),
            keywords=data.get("keywords", []),
            hashtags=data.get("hashtags", []),
            related_topics=data.get("related_topics", []),
            source_trend_id=data.get("source_trend_id", ""),
            confidence=data.get("confidence", 0.5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
        entry.topic_id = data.get("topic_id", entry.topic_id)
        entry.status = data.get("status", "active")
        entry.created_at = data.get("created_at", entry.created_at)
        entry.updated_at = data.get("updated_at", entry.updated_at)
        entry.expires_at = data.get("expires_at", entry.expires_at)
        entry.opportunity_score = data.get("opportunity_score", entry.opportunity_score)
        entry.composite_score = data.get("composite_score", entry.composite_score)
        return entry
