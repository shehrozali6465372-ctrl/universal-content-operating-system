"""
Shared Analytics Models
Frozen interface — v1.0.0
"""

from datetime import datetime, timezone
from typing import List


class EngagementMetrics:
    """Engagement metrics for a single post or time period."""

    __slots__ = (
        "likes", "comments", "shares", "reactions",
        "reach", "impressions", "clicks",
        "engagement_rate", "virality_score",
    )

    def __init__(self):
        self.likes = 0
        self.comments = 0
        self.shares = 0
        self.reactions = 0
        self.reach = 0
        self.impressions = 0
        self.clicks = 0
        self.engagement_rate = 0.0
        self.virality_score = 0.0

    def total_engagement(self) -> int:
        return self.likes + self.comments + self.shares + self.reactions

    def calculate_engagement_rate(self) -> float:
        if self.reach == 0:
            self.engagement_rate = 0.0
        else:
            self.engagement_rate = round(self.total_engagement() / self.reach, 4)
        return self.engagement_rate

    def calculate_virality(self) -> float:
        if self.reach == 0:
            self.virality_score = 0.0
        else:
            self.virality_score = round(self.shares / self.reach, 4)
        return self.virality_score

    def to_dict(self) -> dict:
        return {
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "reactions": self.reactions,
            "reach": self.reach,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "engagement_rate": self.engagement_rate,
            "virality_score": self.virality_score,
            "total_engagement": self.total_engagement(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EngagementMetrics":
        m = cls()
        m.likes = data.get("likes", 0)
        m.comments = data.get("comments", 0)
        m.shares = data.get("shares", 0)
        m.reactions = data.get("reactions", 0)
        m.reach = data.get("reach", 0)
        m.impressions = data.get("impressions", 0)
        m.clicks = data.get("clicks", 0)
        m.engagement_rate = data.get("engagement_rate", 0.0)
        m.virality_score = data.get("virality_score", 0.0)
        return m

    def __repr__(self) -> str:
        return f"EngagementMetrics(engagement={self.total_engagement()}, reach={self.reach})"


class AnalyticsSnapshot:
    """Point-in-time analytics snapshot for tracking performance."""

    __slots__ = (
        "snapshot_id", "post_id", "topic", "niche",
        "metrics", "sentiment", "top_comments",
        "captured_at",
    )

    def __init__(self, post_id: str = "", topic: str = ""):
        self.snapshot_id = f"snap_{int(datetime.now(timezone.utc).timestamp())}"
        self.post_id = post_id
        self.topic = topic
        self.niche = ""
        self.metrics = EngagementMetrics()
        self.sentiment = 0.0
        self.top_comments: List[str] = []
        self.captured_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "post_id": self.post_id,
            "topic": self.topic,
            "niche": self.niche,
            "metrics": self.metrics.to_dict(),
            "sentiment": self.sentiment,
            "top_comments": list(self.top_comments),
            "captured_at": self.captured_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AnalyticsSnapshot":
        s = cls(
            post_id=data.get("post_id", ""),
            topic=data.get("topic", ""),
        )
        s.snapshot_id = data.get("snapshot_id", s.snapshot_id)
        s.niche = data.get("niche", "")
        s.metrics = EngagementMetrics.from_dict(data.get("metrics", {}))
        s.sentiment = data.get("sentiment", 0.0)
        s.top_comments = data.get("top_comments", [])
        s.captured_at = data.get("captured_at", s.captured_at)
        return s

    def __repr__(self) -> str:
        return f"AnalyticsSnapshot(post='{self.post_id}', engagement={self.metrics.total_engagement()})"
