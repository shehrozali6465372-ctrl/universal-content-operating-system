"""TrendAnalyzer — Detect trending niches, boards, pins, seasonal trends."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.analytics_manager.models.analytics_models import TrendData


class TrendAnalyzer:
    def __init__(self):
        self._trends: List[TrendData] = []

    def detect_trend(self, category: str, item: str, current_value: float,
                      previous_value: float, metric: str = "views") -> TrendData:
        change = ((current_value - previous_value) / max(previous_value, 1)) * 100
        direction = "up" if change > 0 else "down"
        trend = TrendData(category=category, item=item, metric=metric,
                           current_value=current_value, previous_value=previous_value,
                           change_pct=round(change, 1), direction=direction)
        self._trends.append(trend)
        return trend

    def get_rising_trends(self, top_k: int = 5) -> List[TrendData]:
        return sorted([t for t in self._trends if t.direction == "up"],
                       key=lambda t: t.change_pct, reverse=True)[:top_k]

    def get_declining_trends(self, top_k: int = 5) -> List[TrendData]:
        return sorted([t for t in self._trends if t.direction == "down"],
                       key=lambda t: t.change_pct)[:top_k]

    def get_stats(self) -> Dict[str, int]:
        return {"total_trends": len(self._trends)}
