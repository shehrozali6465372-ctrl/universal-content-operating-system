"""Platform Memory — Track platform-specific behaviour patterns."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.publishing_memory.publish_history import PublishRecord


class PlatformProfile:
    """Learned behaviour profile for a specific platform."""

    __slots__ = (
        "platform", "total_publishes", "success_rate",
        "best_content_types", "avg_duration_ms",
        "error_frequency", "success_patterns",
    )

    def __init__(self, platform: str = "") -> None:
        self.platform = platform
        self.total_publishes: int = 0
        self.success_rate: float = 0.0
        self.best_content_types: List[str] = []
        self.avg_duration_ms: float = 0.0
        self.error_frequency: Dict[str, int] = {}
        self.success_patterns: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "total_publishes": self.total_publishes,
            "success_rate": round(self.success_rate, 3),
            "best_content_types": self.best_content_types,
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "error_frequency": self.error_frequency,
        }


class PlatformMemory:
    """Track platform-specific publishing behaviour."""

    def __init__(self) -> None:
        self._profiles: Dict[str, PlatformProfile] = {}
        self._records: Dict[str, List[PublishRecord]] = {}

    def observe(self, record: PublishRecord) -> PlatformProfile:
        platform = record.platform
        if platform not in self._profiles:
            self._profiles[platform] = PlatformProfile(platform)
        if platform not in self._records:
            self._records[platform] = []
        self._records[platform].append(record)

        profile = self._profiles[platform]
        records = self._records[platform]
        profile.total_publishes = len(records)
        successes = sum(1 for r in records if r.success)
        profile.success_rate = round(successes / max(1, len(records)), 3)
        durations = [r.duration_ms for r in records if r.duration_ms > 0]
        profile.avg_duration_ms = round(sum(durations) / max(1, len(durations)), 2)

        type_counts: Dict[str, int] = {}
        for r in records:
            type_counts[r.content_type] = type_counts.get(r.content_type, 0) + 1
        profile.best_content_types = sorted(type_counts, key=type_counts.get, reverse=True)[:3]

        return profile

    def get_profile(self, platform: str) -> Optional[PlatformProfile]:
        return self._profiles.get(platform)

    def get_all_profiles(self) -> List[PlatformProfile]:
        return list(self._profiles.values())

    def get_records(self, platform: str) -> List[PublishRecord]:
        return list(self._records.get(platform, []))

    def get_best_platform(self) -> Optional[str]:
        if not self._profiles:
            return None
        return max(self._profiles, key=lambda p: self._profiles[p].success_rate)

    @property
    def platform_count(self) -> int:
        return len(self._profiles)
