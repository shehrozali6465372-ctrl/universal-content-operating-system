"""Publish Plan — Data models for publishing decisions."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class PlatformTarget:
    """A target platform for publishing."""

    __slots__ = (
        "platform", "content_type", "scheduled_time",
        "timezone", "status", "estimated_engagement",
        "priority",
    )

    def __init__(self, platform: str = "", content_type: str = "post") -> None:
        self.platform = platform
        self.content_type = content_type  # post, story, reel, article, thread, etc.
        self.scheduled_time: Optional[float] = None
        self.timezone: str = "UTC"
        self.status = "pending"  # pending, scheduled, published, failed
        self.estimated_engagement: float = 0.0
        self.priority: int = 5  # 1=highest, 10=lowest

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "content_type": self.content_type,
            "scheduled_time": self.scheduled_time,
            "timezone": self.timezone,
            "status": self.status,
            "estimated_engagement": round(self.estimated_engagement, 3),
            "priority": self.priority,
        }


class PublishPlan:
    """Complete publishing plan for content."""

    __slots__ = (
        "plan_id", "content_id", "targets", "created_at",
        "overall_priority", "batch_id", "metadata",
    )

    def __init__(self, plan_id: str = "", content_id: str = "") -> None:
        self.plan_id = plan_id
        self.content_id = content_id
        self.targets: List[PlatformTarget] = []
        self.created_at = time.time()
        self.overall_priority: int = 5
        self.batch_id: str = ""
        self.metadata: Dict[str, Any] = {}

    def add_target(self, target: PlatformTarget) -> None:
        self.targets.append(target)

    def get_target(self, platform: str) -> Optional[PlatformTarget]:
        for t in self.targets:
            if t.platform == platform:
                return t
        return None

    def get_platforms(self) -> List[str]:
        return [t.platform for t in self.targets]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "content_id": self.content_id,
            "targets": [t.to_dict() for t in self.targets],
            "created_at": self.created_at,
            "overall_priority": self.overall_priority,
            "batch_id": self.batch_id,
            "metadata": self.metadata,
        }
