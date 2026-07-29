"""PinAnalyticsTracker — Track impressions, saves, clicks, CTR, outbound clicks per pin."""
from __future__ import annotations
import time
import random
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_pin_manager.models.pin_analytics import PinAnalytics
from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import PinterestPin


class PinAnalyticsTracker:
    """Track and analyze pin performance metrics."""

    def __init__(self) -> None:
        self._records: Dict[str, List[PinAnalytics]] = {}
        self._tracking_log: List[dict] = []

    def record(self, pin_id: str, impressions: int = 0, saves: int = 0,
                clicks: int = 0, outbound_clicks: int = 0) -> PinAnalytics:
        """Record a daily analytics snapshot for a pin."""
        analytics = PinAnalytics(
            pin_id=pin_id,
            impressions=impressions,
            saves=saves,
            clicks=clicks,
            outbound_clicks=outbound_clicks,
        )

        if pin_id not in self._records:
            self._records[pin_id] = []
        self._records[pin_id].append(analytics)

        self._tracking_log.append({
            "pin_id": pin_id,
            "ctr": analytics.ctr,
            "timestamp": time.time(),
        })

        return analytics

    def simulate_daily(self, pin: PinterestPin) -> PinAnalytics:
        """Simulate a day of performance (for testing)."""
        impressions = random.randint(100, 5000)
        saves = random.randint(5, int(impressions * 0.12))
        clicks = random.randint(2, int(impressions * 0.06))
        outbound = random.randint(1, max(clicks // 2, 1))

        # Update pin totals
        pin.total_impressions += impressions
        pin.total_saves += saves
        pin.total_clicks += clicks
        pin.total_outbound_clicks += outbound
        pin.ctr = (pin.total_clicks / max(pin.total_impressions, 1)) * 100

        return self.record(pin.pin_id, impressions, saves, clicks, outbound)

    def get_pin_performance(self, pin_id: str, days: int = 30) -> List[PinAnalytics]:
        records = self._records.get(pin_id, [])
        cutoff = time.time() - (days * 86400)
        return [r for r in records if r.date >= cutoff]

    def get_aggregate(self, pin_id: str, days: int = 30) -> PinAnalytics:
        recent = self.get_pin_performance(pin_id, days)
        return PinAnalytics.aggregate(recent)

    def get_top_pins(self, pins: List[PinterestPin], top_k: int = 5) -> List[PinterestPin]:
        sorted_pins = sorted(pins, key=lambda p: p.ctr, reverse=True)
        return sorted_pins[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "tracked_pins": len(self._records),
            "total_records": sum(len(r) for r in self._records.values()),
        }
