"""Strategy Profile — Data model for a content strategy."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List

_STRAT_COUNTER = itertools.count(1)

STRATEGY_TYPES = (
    "engagement", "growth", "conversion", "brand_awareness",
    "education", "entertainment", "community", "thought_leadership",
)
STRATEGY_STATUSES = ("draft", "active", "testing", "optimized", "deprecated")


class StrategyProfile:
    """A content strategy with targeting and performance data."""

    __slots__ = (
        "strategy_id", "version", "strategy_type", "status", "name",
        "description", "target_platforms", "target_audience",
        "content_pillars", "posting_frequency", "optimal_hours",
        "tone_guidelines", "hashtag_strategy", "engagement_tactics",
        "created_at", "updated_at",
        "usage_count", "success_count", "failure_count",
        "avg_engagement", "avg_reach", "avg_conversion",
        "tags", "metadata", "parent_id",
    )

    def __init__(self, name: str = "", strategy_type: str = "engagement") -> None:
        self.strategy_id: str = f"stg_{next(_STRAT_COUNTER)}"
        self.version: int = 1
        self.strategy_type: str = strategy_type if strategy_type in STRATEGY_TYPES else "engagement"
        self.status: str = "draft"
        self.name: str = name
        self.description: str = ""
        self.target_platforms: List[str] = []
        self.target_audience: str = ""
        self.content_pillars: List[str] = []
        self.posting_frequency: str = "daily"
        self.optimal_hours: List[int] = []
        self.tone_guidelines: str = ""
        self.hashtag_strategy: str = ""
        self.engagement_tactics: List[str] = []
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.usage_count: int = 0
        self.success_count: int = 0
        self.failure_count: int = 0
        self.avg_engagement: float = 0.0
        self.avg_reach: float = 0.0
        self.avg_conversion: float = 0.0
        self.tags: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.parent_id: str = ""

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return round(self.success_count / total, 3)

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def effective_score(self) -> float:
        return round(
            self.avg_engagement * 0.4 + self.avg_reach * 0.3 + self.avg_conversion * 0.3,
            3,
        )

    def record_usage(self, success: bool, engagement: float = 0.0,
                     reach: float = 0.0, conversion: float = 0.0) -> None:
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        n = self.usage_count
        self.avg_engagement = round(((self.avg_engagement * (n - 1)) + engagement) / n, 4)
        self.avg_reach = round(((self.avg_reach * (n - 1)) + reach) / n, 4)
        self.avg_conversion = round(((self.avg_conversion * (n - 1)) + conversion) / n, 4)
        self.updated_at = time.time()

    def fork(self) -> "StrategyProfile":
        child = StrategyProfile(name=self.name, strategy_type=self.strategy_type)
        child.version = self.version + 1
        child.parent_id = self.strategy_id
        child.description = self.description
        child.target_platforms = list(self.target_platforms)
        child.target_audience = self.target_audience
        child.content_pillars = list(self.content_pillars)
        child.posting_frequency = self.posting_frequency
        child.optimal_hours = list(self.optimal_hours)
        child.tone_guidelines = self.tone_guidelines
        child.hashtag_strategy = self.hashtag_strategy
        child.engagement_tactics = list(self.engagement_tactics)
        child.tags = list(self.tags)
        return child

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "strategy_type": self.strategy_type,
            "status": self.status,
            "name": self.name,
            "target_platforms": self.target_platforms,
            "posting_frequency": self.posting_frequency,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "avg_engagement": self.avg_engagement,
            "avg_reach": self.avg_reach,
            "avg_conversion": self.avg_conversion,
            "effective_score": self.effective_score,
            "tags": self.tags,
        }
