"""Writing Plan — Core data model for content planning."""
from __future__ import annotations
import time
from typing import Any, Dict


class WritingPlan:
    """A complete writing plan for a single piece of content.

    Contains all instructions needed by a Draft Generator (Module 2)
    to produce content. This module does NOT generate content — it
    only plans what to write, for whom, and how.
    """
    __slots__ = (
        "plan_id", "topic", "goal", "platform", "audience", "tone",
        "length", "language", "content_type", "strategy", "cta", "hashtags",
        "emoji_level", "structure", "constraints", "metadata",
        "created_at", "updated_at", "version",
    )

    def __init__(self, topic: str = "") -> None:
        self.plan_id = f"plan_{int(time.time() * 1000) % 10000000}"
        self.topic = topic
        self.goal = "educate"         # educate, entertain, inspire, promote, engage
        self.platform = "facebook"
        self.audience = "general"
        self.tone = "friendly"
        self.length = "medium"        # short, medium, long
        self.language = "english"
        self.content_type = "post"    # post, story, reel, carousel, thread
        self.strategy = "educational"  # educational, storytelling, debate, news, tutorial, comparison, case_study, opinion, listicle, qa
        self.cta = "engage"           # engage, share, comment, visit, subscribe
        self.hashtags = True
        self.emoji_level = "medium"   # none, low, medium, high
        self.structure: Dict[str, Any] = {}
        self.constraints: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()
        self.updated_at = time.time()
        self.version = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "topic": self.topic,
            "goal": self.goal,
            "platform": self.platform,
            "audience": self.audience,
            "tone": self.tone,
            "length": self.length,
            "language": self.language,
            "content_type": self.content_type,
            "strategy": self.strategy,
            "cta": self.cta,
            "hashtags": self.hashtags,
            "emoji_level": self.emoji_level,
            "structure": self.structure,
            "constraints": self.constraints,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WritingPlan":
        plan = cls(topic=data.get("topic", ""))
        for field in ("goal", "platform", "audience", "tone", "length",
                       "language", "content_type", "strategy", "cta", "emoji_level"):
            if field in data:
                setattr(plan, field, data[field])
        plan.hashtags = data.get("hashtags", True)
        plan.structure = data.get("structure", {})
        plan.constraints = data.get("constraints", {})
        plan.metadata = data.get("metadata", {})
        if "plan_id" in data:
            plan.plan_id = data["plan_id"]
        return plan

    @property
    def is_valid(self) -> bool:
        return bool(self.topic) and bool(self.goal) and bool(self.platform)
