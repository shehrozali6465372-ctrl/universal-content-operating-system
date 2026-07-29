"""PinterestAnalytics — Track impressions, saves, pin clicks, outbound, board, account performance."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.analytics_manager.models.analytics_models import PinterestAnalyticsData


class PinterestAnalytics:
    def __init__(self):
        self._pins: Dict[str, PinterestAnalyticsData] = {}
        self._lock = threading.Lock()

    def record_pin_performance(self, pin_id: str, board_id: str = "", account_id: str = "",
                                impressions: int = 0, saves: int = 0, clicks: int = 0, outbound: int = 0):
        with self._lock:
            if pin_id not in self._pins:
                self._pins[pin_id] = PinterestAnalyticsData(pin_id=pin_id, board_id=board_id, account_id=account_id)
            p = self._pins[pin_id]
            p.impressions += impressions; p.saves += saves; p.clicks += clicks; p.outbound_clicks += outbound

    def get_top_pins(self, top_k: int = 5) -> List[PinterestAnalyticsData]:
        return sorted(self._pins.values(), key=lambda p: p.clicks, reverse=True)[:top_k]

    def get_pin_stats(self, pin_id: str) -> Optional[PinterestAnalyticsData]:
        return self._pins.get(pin_id)

    def get_summary(self) -> Dict[str, Any]:
        pins = list(self._pins.values())
        return {"total_pins": len(pins), "total_impressions": sum(p.impressions for p in pins),
                "total_saves": sum(p.saves for p in pins), "total_clicks": sum(p.clicks for p in pins)}

    def get_stats(self) -> Dict:
        s = self.get_summary(); return {"total_pins": s["total_pins"], "total_clicks": s["total_clicks"]}
