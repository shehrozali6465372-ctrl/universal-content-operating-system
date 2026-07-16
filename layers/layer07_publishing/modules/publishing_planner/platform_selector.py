"""Platform Selector — Choose best platforms based on content and strategy."""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from layers.layer07_publishing.modules.publishing_planner.publish_plan import PlatformTarget


# Platform suitability scores by content type
PLATFORM_SUITABILITY: Dict[str, Dict[str, float]] = {
    "facebook": {"post": 0.9, "article": 0.7, "video": 0.85, "carousel": 0.8, "story": 0.75, "reel": 0.8},
    "instagram": {"post": 0.9, "reel": 0.95, "carousel": 0.9, "story": 0.85, "video": 0.8},
    "twitter": {"post": 0.95, "thread": 0.9, "video": 0.7, "poll": 0.8},
    "linkedin": {"post": 0.9, "article": 0.95, "video": 0.75, "document": 0.8, "poll": 0.7},
    "tiktok": {"reel": 0.95, "video": 0.9, "post": 0.5},
    "youtube": {"video": 0.95, "short": 0.9, "community": 0.6},
    "pinterest": {"post": 0.85, "video": 0.6, "carousel": 0.9},
    "reddit": {"post": 0.8, "video": 0.5, "poll": 0.7},
    "medium": {"article": 0.95, "post": 0.4},
}

# Platform engagement potential by time of day (UTC hours)
PEAK_HOURS: Dict[str, List[int]] = {
    "facebook": [9, 12, 15, 18, 20],
    "instagram": [7, 12, 17, 19, 21],
    "twitter": [8, 12, 15, 17, 20],
    "linkedin": [7, 8, 12, 17, 18],
    "tiktok": [10, 12, 15, 19, 21],
    "youtube": [12, 15, 18, 20, 21],
    "pinterest": [14, 18, 20, 21, 22],
}


class PlatformSelector:
    """Select best platforms for publishing."""

    def __init__(self) -> None:
        self._select_count = 0

    def select(
        self,
        content_type: str = "post",
        preferred_platforms: Optional[List[str]] = None,
        max_platforms: int = 5,
    ) -> List[PlatformTarget]:
        """Select platforms ranked by suitability."""
        candidates: List[Tuple[str, float]] = []

        target_platforms = preferred_platforms or list(PLATFORM_SUITABILITY.keys())

        for platform in target_platforms:
            suitability = PLATFORM_SUITABILITY.get(platform, {})
            score = suitability.get(content_type, 0.3)
            candidates.append((platform, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        targets = []
        for platform, score in candidates[:max_platforms]:
            target = PlatformTarget(platform=platform, content_type=content_type)
            target.estimated_engagement = score
            targets.append(target)

        self._select_count += 1
        return targets

    def rank_by_engagement(
        self, content_type: str = "post", platforms: Optional[List[str]] = None,
    ) -> List[Tuple[str, float]]:
        """Rank platforms by estimated engagement potential."""
        targets = self.select(content_type, platforms)
        return [(t.platform, t.estimated_engagement) for t in targets]

    def get_peak_hours(self, platform: str) -> List[int]:
        """Get peak engagement hours for a platform."""
        return PEAK_HOURS.get(platform, [9, 12, 18])

    @property
    def select_count(self) -> int:
        return self._select_count
