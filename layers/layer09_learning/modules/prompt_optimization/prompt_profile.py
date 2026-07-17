"""Prompt Profile — Data model for a versioned prompt with performance metadata."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List

_PROFILE_COUNTER = itertools.count(1)

PROMPT_CATEGORIES = (
    "content_generation", "caption", "hook", "cta",
    "hashtag", "seo", "tone", "brand", "strategy",
)
PROMPT_STATUSES = ("draft", "active", "tested", "deprecated", "archived")


class PromptProfile:
    """A single versioned prompt with its performance fingerprint."""

    __slots__ = (
        "profile_id", "version", "category", "status", "template",
        "parameters", "platform", "content_type", "tone",
        "language", "created_at", "updated_at",
        "usage_count", "success_count", "failure_count",
        "avg_engagement", "avg_quality_score", "avg_confidence",
        "tags", "metadata", "parent_id",
    )

    def __init__(
        self,
        template: str = "",
        category: str = "content_generation",
        version: int = 1,
    ) -> None:
        self.profile_id: str = f"pp_{next(_PROFILE_COUNTER)}"
        self.version: int = version
        self.category: str = category if category in PROMPT_CATEGORIES else "content_generation"
        self.status: str = "draft"
        self.template: str = template
        self.parameters: Dict[str, Any] = {}
        self.platform: str = ""
        self.content_type: str = ""
        self.tone: str = ""
        self.language: str = "en"
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.usage_count: int = 0
        self.success_count: int = 0
        self.failure_count: int = 0
        self.avg_engagement: float = 0.0
        self.avg_quality_score: float = 0.0
        self.avg_confidence: float = 0.0
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
        """Composite score: weighted combination of engagement, quality, and confidence."""
        return round(
            self.avg_engagement * 0.4 + self.avg_quality_score * 0.4 + self.avg_confidence * 0.2,
            3,
        )

    def record_usage(self, success: bool, engagement: float = 0.0,
                     quality: float = 0.0, confidence: float = 0.0) -> None:
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        n = self.usage_count
        self.avg_engagement = round(((self.avg_engagement * (n - 1)) + engagement) / n, 4)
        self.avg_quality_score = round(((self.avg_quality_score * (n - 1)) + quality) / n, 4)
        self.avg_confidence = round(((self.avg_confidence * (n - 1)) + confidence) / n, 4)
        self.updated_at = time.time()

    def fork(self) -> "PromptProfile":
        """Create a new version derived from this profile."""
        child = PromptProfile(template=self.template, category=self.category, version=self.version + 1)
        child.parent_id = self.profile_id
        child.parameters = dict(self.parameters)
        child.platform = self.platform
        child.content_type = self.content_type
        child.tone = self.tone
        child.language = self.language
        child.tags = list(self.tags)
        return child

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "category": self.category,
            "status": self.status,
            "template": self.template,
            "platform": self.platform,
            "content_type": self.content_type,
            "tone": self.tone,
            "language": self.language,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "avg_engagement": self.avg_engagement,
            "avg_quality_score": self.avg_quality_score,
            "avg_confidence": self.avg_confidence,
            "effective_score": self.effective_score,
            "tags": self.tags,
        }
