"""Publish History — Record of every published post across all platforms."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List

_HISTORY_COUNTER = itertools.count(1)


class PublishRecord:
    """A single published post record."""

    __slots__ = (
        "record_id", "platform", "post_id", "content_id",
        "content_type", "content_summary", "published_at",
        "status", "success", "duration_ms", "tags",
        "metadata",
    )

    def __init__(
        self,
        platform: str = "",
        post_id: str = "",
        content_id: str = "",
    ) -> None:
        self.record_id: str = f"pm_{next(_HISTORY_COUNTER)}"
        self.platform = platform
        self.post_id = post_id
        self.content_id = content_id
        self.content_type: str = "post"
        self.content_summary: str = ""
        self.published_at: float = time.time()
        self.status: str = "published"
        self.success: bool = True
        self.duration_ms: float = 0.0
        self.tags: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def get_hour(self) -> int:
        return int((self.published_at % 86400) / 3600)

    def get_weekday(self) -> int:
        return int((self.published_at // 86400 + 4) % 7)  # Monday = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "platform": self.platform,
            "post_id": self.post_id,
            "content_id": self.content_id,
            "content_type": self.content_type,
            "content_summary": self.content_summary[:100],
            "published_at": self.published_at,
            "status": self.status,
            "success": self.success,
            "duration_ms": round(self.duration_ms, 2),
            "tags": self.tags,
            "hour": self.get_hour(),
            "weekday": self.get_weekday(),
        }


class PublishHistory:
    """Store and query published post history."""

    def __init__(self, max_records: int = 50000) -> None:
        self._max_records = max_records
        self._records: List[PublishRecord] = []

    def record(self, rec: PublishRecord) -> PublishRecord:
        self._records.append(rec)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
        return rec

    def get_all(self) -> List[PublishRecord]:
        return list(self._records)

    def get_by_platform(self, platform: str) -> List[PublishRecord]:
        return [r for r in self._records if r.platform == platform]

    def get_by_content_id(self, content_id: str) -> List[PublishRecord]:
        return [r for r in self._records if r.content_id == content_id]

    def get_by_status(self, status: str) -> List[PublishRecord]:
        return [r for r in self._records if r.status == status]

    def get_recent(self, count: int = 10) -> List[PublishRecord]:
        return list(self._records[-count:])

    def get_count(self) -> int:
        return len(self._records)

    def get_platform_count(self, platform: str) -> int:
        return sum(1 for r in self._records if r.platform == platform)

    def get_success_rate(self) -> float:
        if not self._records:
            return 1.0
        successes = sum(1 for r in self._records if r.success)
        return round(successes / len(self._records), 3)
