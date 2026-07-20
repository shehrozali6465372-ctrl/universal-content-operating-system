"""PerformanceTracker — Tracks template performance across platforms.

Records impressions, engagements, clicks, and conversion events.
Calculates engagement rate, click rate, and overall score per template.
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from collections import defaultdict

from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate


class PerformanceEvent:
    """A single performance event for a template."""

    __slots__ = ("event_id", "template_id", "event_type", "platform",
                 "impressions", "engagements", "clicks", "conversions",
                 "timestamp", "metadata")

    def __init__(self, template_id: str, event_type: str = "view",
                 platform: str = "facebook") -> None:
        self.event_id: str = f"evt_{int(time.time() * 1000)}"
        self.template_id = template_id
        self.event_type = event_type
        self.platform = platform
        self.impressions: int = 0
        self.engagements: int = 0
        self.clicks: int = 0
        self.conversions: int = 0
        self.timestamp: float = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "template_id": self.template_id,
            "event_type": self.event_type,
            "platform": self.platform,
            "impressions": self.impressions,
            "engagements": self.engagements,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "timestamp": self.timestamp,
        }


class PerformanceTracker:
    """Tracks performance of templates across all platforms."""

    def __init__(self) -> None:
        self._events: List[PerformanceEvent] = []
        self._by_template: Dict[str, List[PerformanceEvent]] = defaultdict(list)
        self._by_platform: Dict[str, List[PerformanceEvent]] = defaultdict(list)

    def record_event(
        self,
        template_id: str,
        platform: str = "facebook",
        impressions: int = 0,
        engagements: int = 0,
        clicks: int = 0,
        conversions: int = 0,
    ) -> PerformanceEvent:
        """Record a performance event for a template."""
        event = PerformanceEvent(template_id, "performance", platform)
        event.impressions = impressions
        event.engagements = engagements
        event.clicks = clicks
        event.conversions = conversions

        self._events.append(event)
        self._by_template[template_id].append(event)
        self._by_platform[platform].append(event)
        return event

    def record_post_published(
        self, template_id: str, platform: str,
        impressions: int, engagements: int, clicks: int,
    ) -> PerformanceEvent:
        """Record that a post was published and got initial metrics."""
        return self.record_event(
            template_id, platform, impressions, engagements, clicks,
        )

    def record_update(
        self, template_id: str, platform: str,
        impressions: int = 0, engagements: int = 0, clicks: int = 0,
    ) -> PerformanceEvent:
        """Record updated metrics (e.g., after 24h)."""
        return self.record_event(
            template_id, platform, impressions, engagements, clicks,
        )

    def get_template_stats(self, template_id: str) -> Dict[str, Any]:
        """Get aggregated stats for a template."""
        events = self._by_template.get(template_id, [])
        total_imp = sum(e.impressions for e in events)
        total_eng = sum(e.engagements for e in events)
        total_clicks = sum(e.clicks for e in events)
        total_conv = sum(e.conversions for e in events)

        eng_rate = total_eng / total_imp if total_imp > 0 else 0.0
        click_rate = total_clicks / total_imp if total_imp > 0 else 0.0
        conv_rate = total_conv / total_imp if total_imp > 0 else 0.0

        return {
            "template_id": template_id,
            "total_events": len(events),
            "total_impressions": total_imp,
            "total_engagements": total_eng,
            "total_clicks": total_clicks,
            "total_conversions": total_conv,
            "engagement_rate": round(eng_rate, 4),
            "click_rate": round(click_rate, 4),
            "conversion_rate": round(conv_rate, 4),
        }

    def get_platform_stats(self, platform: str) -> Dict[str, Any]:
        """Get aggregated stats for a platform."""
        events = self._by_platform.get(platform, [])
        total_imp = sum(e.impressions for e in events)
        total_eng = sum(e.engagements for e in events)
        total_clicks = sum(e.clicks for e in events)

        return {
            "platform": platform,
            "total_events": len(events),
            "total_impressions": total_imp,
            "total_engagements": total_eng,
            "total_clicks": total_clicks,
            "engagement_rate": round(total_eng / total_imp, 4) if total_imp > 0 else 0.0,
            "click_rate": round(total_clicks / total_imp, 4) if total_imp > 0 else 0.0,
        }

    def get_top_performers(self, platform: Optional[str] = None,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Get top-performing templates by engagement rate."""
        template_ids = set()
        for tid, events in self._by_template.items():
            if platform:
                events = [e for e in events if e.platform == platform]
            if events:
                template_ids.add(tid)

        stats = []
        for tid in template_ids:
            s = self.get_template_stats(tid)
            if platform:
                plat_events = [e for e in self._by_template[tid] if e.platform == platform]
                total_imp = sum(e.impressions for e in plat_events)
                total_eng = sum(e.engagements for e in plat_events)
                s["engagement_rate"] = round(total_eng / total_imp, 4) if total_imp > 0 else 0.0
            stats.append(s)

        stats.sort(key=lambda x: x["engagement_rate"], reverse=True)
        return stats[:limit]

    def get_event_count(self) -> int:
        """Total events recorded."""
        return len(self._events)

    def update_template_from_events(self, template: PromptTemplate) -> None:
        """Update a template's metrics from recorded events."""
        stats = self.get_template_stats(template.template_id)
        template.total_impressions = stats["total_impressions"]
        template.total_engagements = stats["total_engagements"]
        template.total_clicks = stats["total_clicks"]
        template._recalculate_score()
