"""
Competitor Profile Model
Layer 2: Research Engine — Module 3

Rich data model for a Facebook competitor with multi-dimensional analysis.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional


class CompetitorProfile:
    """Full competitor intelligence profile."""

    __slots__ = (
        "competitor_id", "page_name", "page_url", "niche",
        "category", "followers", "following", "post_count",
        "posting_frequency", "best_post_times", "avg_posts_per_day",
        "top_topics", "top_hashtags", "top_formats",
        "writing_style", "tone", "image_style", "brand_colors",
        "avg_engagement_rate", "avg_likes", "avg_comments", "avg_shares",
        "engagement_trend", "growth_score", "opportunity_score",
        "content_gaps", "weaknesses", "strengths",
        "confidence", "data_quality",
        "status", "tags", "metadata",
        "created_at", "updated_at", "last_analyzed",
    )

    NICHES = [
        "finance", "technology", "health", "lifestyle",
        "education", "entertainment", "business", "marketing",
        "ai", "crypto", "fitness", "cooking", "travel",
        "parenting", "motivation", "general",
    ]

    STATUSES = ["active", "inactive", "archived", "monitoring"]

    ENGAGEMENT_TRENDS = ["growing", "stable", "declining", "unknown"]

    def __init__(
        self,
        page_name: str,
        page_url: str = "",
        niche: str = "general",
        category: str = "general",
        followers: int = 0,
        following: int = 0,
        post_count: int = 0,
        posting_frequency: str = "unknown",
        best_post_times: Optional[List[str]] = None,
        avg_posts_per_day: float = 0.0,
        top_topics: Optional[List[str]] = None,
        top_hashtags: Optional[List[str]] = None,
        top_formats: Optional[List[str]] = None,
        writing_style: str = "unknown",
        tone: str = "neutral",
        image_style: str = "unknown",
        brand_colors: Optional[List[str]] = None,
        avg_engagement_rate: float = 0.0,
        avg_likes: float = 0.0,
        avg_comments: float = 0.0,
        avg_shares: float = 0.0,
        engagement_trend: str = "unknown",
        growth_score: float = 0.0,
        confidence: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ):
        self.competitor_id = f"comp_{page_name.lower().replace(' ', '_')}_{int(datetime.now(timezone.utc).timestamp())}"
        self.page_name = page_name
        self.page_url = page_url
        self.niche = niche if niche in self.NICHES else "general"
        self.category = category
        self.followers = max(0, followers)
        self.following = max(0, following)
        self.post_count = max(0, post_count)
        self.posting_frequency = posting_frequency
        self.best_post_times = best_post_times or []
        self.avg_posts_per_day = max(0.0, avg_posts_per_day)
        self.top_topics = top_topics or []
        self.top_hashtags = top_hashtags or []
        self.top_formats = top_formats or []
        self.writing_style = writing_style
        self.tone = tone
        self.image_style = image_style
        self.brand_colors = brand_colors or []
        self.avg_engagement_rate = max(0.0, min(100.0, avg_engagement_rate))
        self.avg_likes = max(0.0, avg_likes)
        self.avg_comments = max(0.0, avg_comments)
        self.avg_shares = max(0.0, avg_shares)
        self.engagement_trend = engagement_trend if engagement_trend in self.ENGAGEMENT_TRENDS else "unknown"
        self.growth_score = self._clamp(growth_score)
        self.opportunity_score = 0.0
        self.content_gaps: List[str] = []
        self.weaknesses: List[str] = []
        self.strengths: List[str] = []
        self.confidence = max(0.0, min(1.0, confidence))
        self.data_quality = "initial"
        self.status = "active"
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.last_analyzed = self.created_at

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
        return max(low, min(high, value))

    def calculate_opportunity_score(self) -> float:
        """Calculate opportunity based on growth potential vs competition."""
        # High followers + declining engagement = opportunity
        # Low followers + growing engagement = watch
        engagement_factor = self.avg_engagement_rate / 10.0 if self.avg_engagement_rate > 0 else 0
        growth_factor = self.growth_score / 10.0
        gap_factor = min(len(self.content_gaps) / 5.0, 1.0)
        weakness_factor = min(len(self.weaknesses) / 5.0, 1.0)

        self.opportunity_score = round(
            self._clamp(
                (engagement_factor * 0.2) +
                (growth_factor * 0.2) +
                (gap_factor * 0.3) +
                (weakness_factor * 0.3)
            ),
            2,
        )
        return self.opportunity_score

    def get_engagement_total(self) -> float:
        """Total average engagement per post."""
        return self.avg_likes + self.avg_comments + self.avg_shares

    def get_follower_tier(self) -> str:
        """Categorize by follower count."""
        if self.followers >= 1_000_000:
            return "mega"
        elif self.followers >= 100_000:
            return "large"
        elif self.followers >= 10_000:
            return "medium"
        elif self.followers >= 1_000:
            return "small"
        return "micro"

    def is_analyzable(self) -> bool:
        """Check if enough data exists for meaningful analysis."""
        return (
            self.followers > 0
            and self.post_count > 0
            and self.confidence >= 0.3
        )

    def to_dict(self) -> dict:
        return {
            "competitor_id": self.competitor_id,
            "page_name": self.page_name,
            "page_url": self.page_url,
            "niche": self.niche,
            "category": self.category,
            "followers": self.followers,
            "following": self.following,
            "post_count": self.post_count,
            "posting_frequency": self.posting_frequency,
            "best_post_times": self.best_post_times,
            "avg_posts_per_day": self.avg_posts_per_day,
            "top_topics": self.top_topics,
            "top_hashtags": self.top_hashtags,
            "top_formats": self.top_formats,
            "writing_style": self.writing_style,
            "tone": self.tone,
            "image_style": self.image_style,
            "brand_colors": self.brand_colors,
            "avg_engagement_rate": self.avg_engagement_rate,
            "avg_likes": self.avg_likes,
            "avg_comments": self.avg_comments,
            "avg_shares": self.avg_shares,
            "engagement_trend": self.engagement_trend,
            "growth_score": self.growth_score,
            "opportunity_score": self.opportunity_score,
            "content_gaps": self.content_gaps,
            "weaknesses": self.weaknesses,
            "strengths": self.strengths,
            "confidence": self.confidence,
            "data_quality": self.data_quality,
            "status": self.status,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_analyzed": self.last_analyzed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompetitorProfile":
        p = cls(
            page_name=data["page_name"],
            page_url=data.get("page_url", ""),
            niche=data.get("niche", "general"),
            category=data.get("category", "general"),
            followers=data.get("followers", 0),
            following=data.get("following", 0),
            post_count=data.get("post_count", 0),
            posting_frequency=data.get("posting_frequency", "unknown"),
            best_post_times=data.get("best_post_times", []),
            avg_posts_per_day=data.get("avg_posts_per_day", 0.0),
            top_topics=data.get("top_topics", []),
            top_hashtags=data.get("top_hashtags", []),
            top_formats=data.get("top_formats", []),
            writing_style=data.get("writing_style", "unknown"),
            tone=data.get("tone", "neutral"),
            image_style=data.get("image_style", "unknown"),
            brand_colors=data.get("brand_colors", []),
            avg_engagement_rate=data.get("avg_engagement_rate", 0.0),
            avg_likes=data.get("avg_likes", 0.0),
            avg_comments=data.get("avg_comments", 0.0),
            avg_shares=data.get("avg_shares", 0.0),
            engagement_trend=data.get("engagement_trend", "unknown"),
            growth_score=data.get("growth_score", 0.0),
            confidence=data.get("confidence", 0.5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
        p.competitor_id = data.get("competitor_id", p.competitor_id)
        p.opportunity_score = data.get("opportunity_score", 0.0)
        p.content_gaps = data.get("content_gaps", [])
        p.weaknesses = data.get("weaknesses", [])
        p.strengths = data.get("strengths", [])
        p.data_quality = data.get("data_quality", "initial")
        p.status = data.get("status", "active")
        p.created_at = data.get("created_at", p.created_at)
        p.updated_at = data.get("updated_at", p.updated_at)
        p.last_analyzed = data.get("last_analyzed", p.last_analyzed)
        return p
