"""Memory Retention — Archive, cleanup, compression, expiration policy."""
from __future__ import annotations
import time
from typing import Any, Dict, List

from layers.layer07_publishing.modules.publishing_memory.publish_history import (
    PublishHistory, PublishRecord,
)


class RetentionPolicy:
    """Configuration for memory retention."""

    __slots__ = ("max_records", "retention_days", "archive_after_days",
                 "compress_after_days")

    def __init__(
        self,
        max_records: int = 10000,
        retention_days: int = 365,
        archive_after_days: int = 90,
        compress_after_days: int = 30,
    ) -> None:
        self.max_records = max_records
        self.retention_days = retention_days
        self.archive_after_days = archive_after_days
        self.compress_after_days = compress_after_days

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_records": self.max_records,
            "retention_days": self.retention_days,
            "archive_after_days": self.archive_after_days,
            "compress_after_days": self.compress_after_days,
        }


class ArchiveRecord:
    """Archived (compressed) record — stores summary only."""

    __slots__ = ("platform", "content_type", "success", "published_at", "tags")

    def __init__(self, rec: PublishRecord) -> None:
        self.platform = rec.platform
        self.content_type = rec.content_type
        self.success = rec.success
        self.published_at = rec.published_at
        self.tags = list(rec.tags)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "content_type": self.content_type,
            "success": self.success,
            "published_at": self.published_at,
            "tags": self.tags,
        }


class MemoryRetention:
    """Manage memory lifecycle: archive, cleanup, compression."""

    def __init__(self, policy: RetentionPolicy | None = None) -> None:
        self.policy = policy or RetentionPolicy()
        self._archives: List[ArchiveRecord] = []
        self._cleanup_count = 0
        self._archive_count = 0

    def cleanup(self, history: PublishHistory) -> int:
        cutoff = time.time() - (self.policy.retention_days * 86400)
        records = history.get_all()
        removed = 0
        for rec in records:
            if rec.published_at < cutoff:
                removed += 1
        excess = max(0, len(records) - self.policy.max_records)
        self._cleanup_count += removed + excess
        return removed + excess

    def archive(self, records: List[PublishRecord]) -> int:
        archive_cutoff = time.time() - (self.policy.archive_after_days * 86400)
        archived = 0
        for rec in records:
            if rec.published_at < archive_cutoff:
                self._archives.append(ArchiveRecord(rec))
                archived += 1
        self._archive_count += archived
        return archived

    def should_compress(self, record: PublishRecord) -> bool:
        age_days = (time.time() - record.published_at) / 86400
        return age_days >= self.policy.compress_after_days

    def get_archives(self) -> List[ArchiveRecord]:
        return list(self._archives)

    @property
    def cleanup_count(self) -> int:
        return self._cleanup_count

    @property
    def archive_count(self) -> int:
        return self._archive_count
