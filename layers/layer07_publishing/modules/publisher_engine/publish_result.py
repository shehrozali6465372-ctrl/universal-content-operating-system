"""Publish Result — Extended result model for the publisher engine."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_RESULT_COUNTER = itertools.count(1)


class PublisherResult:
    """Extended result for a publishing operation."""

    __slots__ = (
        "result_id", "success", "post_id", "url", "platform",
        "media_ids", "error_message", "error_category",
        "duration_ms", "idempotency_key", "metadata",
    )

    def __init__(self, success: bool = False, platform: str = "") -> None:
        self.result_id: str = f"res_{next(_RESULT_COUNTER)}"
        self.success = success
        self.post_id: str = ""
        self.url: str = ""
        self.platform = platform
        self.media_ids: List[str] = []
        self.error_message: str = ""
        self.error_category: str = ""
        self.duration_ms: float = 0.0
        self.idempotency_key: str = ""
        self.metadata: Dict[str, Any] = {}

    def set_error(self, message: str, category: str = "unknown") -> None:
        self.success = False
        self.error_message = message[:500]
        self.error_category = category

    def set_success(self, post_id: str, url: str = "") -> None:
        self.success = True
        self.post_id = post_id
        self.url = url
        self.error_message = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "success": self.success,
            "post_id": self.post_id,
            "url": self.url,
            "platform": self.platform,
            "media_ids": self.media_ids,
            "error_message": self.error_message,
            "error_category": self.error_category,
            "duration_ms": round(self.duration_ms, 2),
            "idempotency_key": self.idempotency_key,
        }
