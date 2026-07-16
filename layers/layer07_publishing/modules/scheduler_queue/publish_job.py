"""Publish Job — Job model for the publishing queue."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


JOB_STATUSES = ("pending", "scheduled", "running", "completed", "failed", "cancelled", "dead")
JOB_PRIORITIES = {"critical": 1, "high": 3, "normal": 5, "low": 7, "background": 10}


class PublishJob:
    """A single publishing job in the queue."""

    __slots__ = (
        "job_id", "content_id", "platform", "content", "content_type",
        "media_paths", "scheduled_time", "status", "priority",
        "attempts", "max_retries", "last_error", "created_at",
        "started_at", "completed_at", "metadata",
    )

    def __init__(
        self,
        job_id: str = "",
        content_id: str = "",
        platform: str = "",
        content: str = "",
    ) -> None:
        self.job_id = job_id
        self.content_id = content_id
        self.platform = platform
        self.content = content
        self.content_type: str = "post"
        self.media_paths: List[str] = []
        self.scheduled_time: Optional[float] = None
        self.status: str = "pending"
        self.priority: int = JOB_PRIORITIES["normal"]
        self.attempts: int = 0
        self.max_retries: int = 3
        self.last_error: str = ""
        self.created_at: float = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.metadata: Dict[str, Any] = {}

    def is_ready(self) -> bool:
        if self.status != "scheduled":
            return False
        return self.scheduled_time is not None and time.time() >= self.scheduled_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "content_id": self.content_id,
            "platform": self.platform,
            "content_type": self.content_type,
            "status": self.status,
            "priority": self.priority,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "scheduled_time": self.scheduled_time,
            "created_at": self.created_at,
            "last_error": self.last_error[:100],
        }
