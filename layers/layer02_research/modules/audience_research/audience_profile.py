"""
Audience Profile Model
Layer 2: Research Engine — Module 4

Rich data model for a Facebook audience segment with demographics, interests, and behavior.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional


class AudienceProfile:
    """A Facebook audience segment with full intelligence."""

    __slots__ = (
        "profile_id", "segment_name", "niche", "category",
        "age_range", "gender_split", "locations", "languages",
        "interests", "sub_interests", "behaviors",
        "online_hours", "peak_engagement_hours", "device_split",
        "content_preferences", "format_preferences",
        "avg_session_duration", "avg_posts_interacted",
        "engagement_rate", "growth_rate",
        "size_estimate", "growth_trend",
        "personas", "pain_points", "desires",
        "buying_stage", "confidence",
        "status", "tags", "metadata",
        "created_at", "updated_at", "last_analyzed",
    )

    BUYING_STAGES = [
        "awareness", "consideration", "decision",
        "retention", "advocacy", "unknown",
    ]

    STATUSES = ["active", "inactive", "archived", "growing", "declining"]

    GROWTH_TRENDS = ["growing", "stable", "declining", "unknown"]

    def __init__(
        self,
        segment_name: str,
        niche: str = "general",
        category: str = "general",
        age_range: Optional[List[int]] = None,
        gender_split: Optional[Dict[str, float]] = None,
        locations: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        interests: Optional[List[str]] = None,
        sub_interests: Optional[List[str]] = None,
        behaviors: Optional[List[str]] = None,
        online_hours: Optional[List[int]] = None,
        peak_engagement_hours: Optional[List[int]] = None,
        device_split: Optional[Dict[str, float]] = None,
        content_preferences: Optional[List[str]] = None,
        format_preferences: Optional[List[str]] = None,
        avg_session_duration: float = 0.0,
        avg_posts_interacted: float = 0.0,
        engagement_rate: float = 0.0,
        growth_rate: float = 0.0,
        size_estimate: int = 0,
        growth_trend: str = "unknown",
        personas: Optional[List[Dict]] = None,
        pain_points: Optional[List[str]] = None,
        desires: Optional[List[str]] = None,
        buying_stage: str = "unknown",
        confidence: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ):
        self.profile_id = f"aud_{segment_name.lower().replace(' ', '_')}_{int(datetime.now(timezone.utc).timestamp())}"
        self.segment_name = segment_name
        self.niche = niche
        self.category = category
        self.age_range = age_range or [18, 65]
        self.gender_split = gender_split or {"male": 50.0, "female": 50.0}
        self.locations = locations or []
        self.languages = languages or []
        self.interests = interests or []
        self.sub_interests = sub_interests or []
        self.behaviors = behaviors or []
        self.online_hours = online_hours or []
        self.peak_engagement_hours = peak_engagement_hours or []
        self.device_split = device_split or {"mobile": 70.0, "desktop": 30.0}
        self.content_preferences = content_preferences or []
        self.format_preferences = format_preferences or []
        self.avg_session_duration = max(0.0, avg_session_duration)
        self.avg_posts_interacted = max(0.0, avg_posts_interacted)
        self.engagement_rate = max(0.0, min(100.0, engagement_rate))
        self.growth_rate = growth_rate
        self.size_estimate = max(0, size_estimate)
        self.growth_trend = growth_trend if growth_trend in self.GROWTH_TRENDS else "unknown"
        self.personas = personas or []
        self.pain_points = pain_points or []
        self.desires = desires or []
        self.buying_stage = buying_stage if buying_stage in self.BUYING_STAGES else "unknown"
        self.confidence = max(0.0, min(1.0, confidence))
        self.status = "active"
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.last_analyzed = self.created_at

    def get_age_midpoint(self) -> float:
        if len(self.age_range) >= 2:
            return (self.age_range[0] + self.age_range[1]) / 2.0
        return 35.0

    def get_mobile_percentage(self) -> float:
        return self.device_split.get("mobile", 0.0)

    def is_high_value(self) -> bool:
        return (
            self.engagement_rate >= 5.0
            and self.confidence >= 0.6
            and self.size_estimate >= 1000
        )

    def is_growing(self) -> bool:
        return self.growth_trend == "growing" or self.growth_rate > 5.0

    def get_size_tier(self) -> str:
        if self.size_estimate >= 1_000_000:
            return "massive"
        elif self.size_estimate >= 100_000:
            return "large"
        elif self.size_estimate >= 10_000:
            return "medium"
        elif self.size_estimate >= 1_000:
            return "small"
        return "niche"

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "segment_name": self.segment_name,
            "niche": self.niche,
            "category": self.category,
            "age_range": self.age_range,
            "gender_split": self.gender_split,
            "locations": self.locations,
            "languages": self.languages,
            "interests": self.interests,
            "sub_interests": self.sub_interests,
            "behaviors": self.behaviors,
            "online_hours": self.online_hours,
            "peak_engagement_hours": self.peak_engagement_hours,
            "device_split": self.device_split,
            "content_preferences": self.content_preferences,
            "format_preferences": self.format_preferences,
            "avg_session_duration": self.avg_session_duration,
            "avg_posts_interacted": self.avg_posts_interacted,
            "engagement_rate": self.engagement_rate,
            "growth_rate": self.growth_rate,
            "size_estimate": self.size_estimate,
            "growth_trend": self.growth_trend,
            "personas": self.personas,
            "pain_points": self.pain_points,
            "desires": self.desires,
            "buying_stage": self.buying_stage,
            "confidence": self.confidence,
            "status": self.status,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_analyzed": self.last_analyzed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AudienceProfile":
        p = cls(
            segment_name=data["segment_name"],
            niche=data.get("niche", "general"),
            category=data.get("category", "general"),
            age_range=data.get("age_range", [18, 65]),
            gender_split=data.get("gender_split", {}),
            locations=data.get("locations", []),
            languages=data.get("languages", []),
            interests=data.get("interests", []),
            sub_interests=data.get("sub_interests", []),
            behaviors=data.get("behaviors", []),
            online_hours=data.get("online_hours", []),
            peak_engagement_hours=data.get("peak_engagement_hours", []),
            device_split=data.get("device_split", {}),
            content_preferences=data.get("content_preferences", []),
            format_preferences=data.get("format_preferences", []),
            avg_session_duration=data.get("avg_session_duration", 0.0),
            avg_posts_interacted=data.get("avg_posts_interacted", 0.0),
            engagement_rate=data.get("engagement_rate", 0.0),
            growth_rate=data.get("growth_rate", 0.0),
            size_estimate=data.get("size_estimate", 0),
            growth_trend=data.get("growth_trend", "unknown"),
            personas=data.get("personas", []),
            pain_points=data.get("pain_points", []),
            desires=data.get("desires", []),
            buying_stage=data.get("buying_stage", "unknown"),
            confidence=data.get("confidence", 0.5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
        p.profile_id = data.get("profile_id", p.profile_id)
        p.status = data.get("status", "active")
        p.created_at = data.get("created_at", p.created_at)
        p.updated_at = data.get("updated_at", p.updated_at)
        p.last_analyzed = data.get("last_analyzed", p.last_analyzed)
        return p
