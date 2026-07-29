"""ContentAnalytics — Analyze best/worst articles, trending topics, evergreen content."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.analytics_manager.models.analytics_models import ContentAnalyticsData


class ContentAnalytics:
    def __init__(self):
        self._articles: Dict[str, ContentAnalyticsData] = {}
        self._lock = threading.Lock()

    def record_article(self, article_id: str, title: str = "", views: int = 0,
                        pins: int = 0, clicks: int = 0, revenue: float = 0.0):
        with self._lock:
            if article_id not in self._articles:
                self._articles[article_id] = ContentAnalyticsData(article_id=article_id, title=title)
            a = self._articles[article_id]
            a.total_views += views; a.total_pins += pins; a.total_clicks += clicks; a.total_revenue += revenue
            if a.total_views > 1000 and a.total_clicks > 50: a.is_evergreen = True
            if views > 100: a.trend = "rising"
            elif views < 10: a.trend = "declining"
            else: a.trend = "stable"

    def get_best_articles(self, top_k: int = 5) -> List[ContentAnalyticsData]:
        return sorted(self._articles.values(), key=lambda a: a.total_views, reverse=True)[:top_k]

    def get_worst_articles(self, top_k: int = 5) -> List[ContentAnalyticsData]:
        return sorted(self._articles.values(), key=lambda a: a.total_views)[:top_k]

    def get_trending_topics(self, top_k: int = 5) -> List[ContentAnalyticsData]:
        return [a for a in sorted(self._articles.values(), key=lambda x: x.total_views, reverse=True) if a.trend == "rising"][:top_k]

    def get_evergreen(self) -> List[ContentAnalyticsData]:
        return [a for a in self._articles.values() if a.is_evergreen]

    def get_summary(self) -> Dict[str, Any]:
        arts = list(self._articles.values())
        return {"total_articles": len(arts), "total_views": sum(a.total_views for a in arts),
                "evergreen": len(self.get_evergreen()), "trending": len(self.get_trending_topics())}

    def get_stats(self) -> Dict:
        s = self.get_summary(); return {"total_articles": s["total_articles"]}
