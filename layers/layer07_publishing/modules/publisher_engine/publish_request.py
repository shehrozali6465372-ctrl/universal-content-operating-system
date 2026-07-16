"""Publish Request — Data model for publishing requests."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset

_REQUEST_COUNTER = itertools.count(1)


class PublishRequest:
    """A validated, ready-to-execute publishing request."""

    __slots__ = (
        "request_id", "platform", "content", "content_type",
        "media_assets", "scheduled_time", "idempotency_key",
        "metadata", "created_at", "priority", "scheduled",
    )

    def __init__(
        self,
        platform: str = "",
        content: str = "",
        content_type: str = "post",
    ) -> None:
        self.request_id: str = f"req_{next(_REQUEST_COUNTER)}"
        self.platform = platform
        self.content = content
        self.content_type = content_type
        self.media_assets: List[MediaAsset] = []
        self.scheduled_time: Optional[float] = None
        self.idempotency_key: str = ""
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.priority: int = 5
        self.scheduled: bool = False

    def has_media(self) -> bool:
        return len(self.media_assets) > 0

    def get_media_paths(self) -> List[str]:
        return [m.file_path for m in self.media_assets if m.file_path]

    def validate(self) -> List[str]:
        """Return list of validation errors (empty = valid)."""
        errors: List[str] = []
        if not self.platform:
            errors.append("Platform is required")
        if not self.content and not self.media_assets:
            errors.append("Content or media is required")
        if len(self.content) > 50000:
            errors.append("Content exceeds 50000 character limit")
        if self.scheduled and self.scheduled_time is not None:
            if self.scheduled_time <= time.time():
                errors.append("Scheduled time must be in the future")
        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "platform": self.platform,
            "content_type": self.content_type,
            "content_length": len(self.content),
            "media_count": len(self.media_assets),
            "scheduled": self.scheduled,
            "scheduled_time": self.scheduled_time,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at,
            "priority": self.priority,
        }
