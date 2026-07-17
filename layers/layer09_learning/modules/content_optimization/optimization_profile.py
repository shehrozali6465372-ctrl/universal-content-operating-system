"""Optimization Profile — Content optimization configuration and goals."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List

_OP_COUNTER = itertools.count(1)

OPTIMIZATION_GOALS = ("engagement", "readability", "seo", "conversion", "brand_consistency", "virality")
OPTIMIZATION_LEVELS = ("light", "moderate", "aggressive")


class OptimizationProfile:
    """Configuration for a content optimization run."""

    __slots__ = ("profile_id", "goal", "level", "platform", "content_type",
                 "target_audience", "constraints", "max_suggestions",
                 "preserve_meaning", "preserve_hashtags",
                 "created_at", "updated_at", "tags")

    def __init__(self, goal: str = "engagement", level: str = "moderate") -> None:
        self.profile_id: str = f"op_{next(_OP_COUNTER)}"
        self.goal = goal if goal in OPTIMIZATION_GOALS else "engagement"
        self.level = level if level in OPTIMIZATION_LEVELS else "moderate"
        self.platform: str = ""
        self.content_type: str = ""
        self.target_audience: str = ""
        self.constraints: List[str] = []
        self.max_suggestions: int = 5
        self.preserve_meaning: bool = True
        self.preserve_hashtags: bool = False
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.tags: List[str] = []

    @property
    def is_aggressive(self) -> bool:
        return self.level == "aggressive"

    def add_constraint(self, constraint: str) -> None:
        if constraint not in self.constraints:
            self.constraints.append(constraint)
            self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "goal": self.goal,
            "level": self.level,
            "platform": self.platform,
            "content_type": self.content_type,
            "max_suggestions": self.max_suggestions,
            "preserve_meaning": self.preserve_meaning,
            "preserve_hashtags": self.preserve_hashtags,
            "constraints": self.constraints,
        }
