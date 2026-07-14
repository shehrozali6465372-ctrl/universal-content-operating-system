"""
Shared Topic Models
Frozen interface — v1.0.0
"""

from datetime import datetime, timezone
from typing import List, Optional


class Topic:
    """Represents a research topic."""

    __slots__ = (
        "topic_id", "title", "description", "niche",
        "keywords", "tags", "source", "created_at",
    )

    def __init__(
        self,
        title: str,
        description: str = "",
        niche: str = "general",
        keywords: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        source: str = "",
    ):
        self.topic_id = f"topic_{hash(title) % 1000000}"
        self.title = title
        self.description = description
        self.niche = niche
        self.keywords = keywords or []
        self.tags = tags or []
        self.source = source
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "topic_id": self.topic_id,
            "title": self.title,
            "description": self.description,
            "niche": self.niche,
            "keywords": list(self.keywords),
            "tags": list(self.tags),
            "source": self.source,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Topic":
        t = cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            niche=data.get("niche", "general"),
            keywords=data.get("keywords", []),
            tags=data.get("tags", []),
            source=data.get("source", ""),
        )
        t.topic_id = data.get("topic_id", t.topic_id)
        t.created_at = data.get("created_at", t.created_at)
        return t

    def __repr__(self) -> str:
        return f"Topic(title='{self.title}', niche='{self.niche}')"


class TopicScore:
    """Scored topic with multi-factor assessment."""

    __slots__ = (
        "topic", "overall_score", "trend_score", "competition_score",
        "audience_score", "knowledge_score", "verification_score",
        "opportunity_score", "risk_score", "confidence",
        "recommendation", "computed_at",
    )

    RECOMMENDATIONS = ["strong_publish", "publish", "conditional_publish", "revise", "skip"]

    def __init__(self, topic: Topic, overall_score: float = 0.0):
        self.topic = topic
        self.overall_score = max(0.0, min(100.0, overall_score))
        self.trend_score = 0.0
        self.competition_score = 0.0
        self.audience_score = 0.0
        self.knowledge_score = 0.0
        self.verification_score = 0.0
        self.opportunity_score = 0.0
        self.risk_score = 0.0
        self.confidence = 0.0
        self.recommendation = "skip"
        self.computed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "topic": self.topic.to_dict(),
            "overall_score": self.overall_score,
            "trend_score": self.trend_score,
            "competition_score": self.competition_score,
            "audience_score": self.audience_score,
            "knowledge_score": self.knowledge_score,
            "verification_score": self.verification_score,
            "opportunity_score": self.opportunity_score,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "computed_at": self.computed_at,
        }

    def should_publish(self) -> bool:
        return self.recommendation in ("strong_publish", "publish")

    def __repr__(self) -> str:
        return f"TopicScore(title='{self.topic.title}', score={self.overall_score}, rec='{self.recommendation}')"
