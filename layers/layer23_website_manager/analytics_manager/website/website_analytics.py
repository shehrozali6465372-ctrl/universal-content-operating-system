"""WebsiteAnalytics — Track articles, views, sessions, bounce rate, avg time, top pages."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.analytics_manager.models.analytics_models import WebsiteAnalyticsData


class WebsiteAnalytics:
    def __init__(self):
        self._pages: Dict[str, WebsiteAnalyticsData] = {}
        self._lock = threading.Lock()

    def record_page_view(self, article_id: str, title: str = "", session_duration: float = 0.0, bounced: bool = False, source: str = ""):
        with self._lock:
            if article_id not in self._pages:
                self._pages[article_id] = WebsiteAnalyticsData(article_id=article_id, title=title)
            p = self._pages[article_id]
            p.views += 1; p.sessions += 1
            p.avg_time_on_page = ((p.avg_time_on_page * (p.sessions - 1)) + session_duration) / p.sessions
            if bounced: p.bounce_rate = ((p.bounce_rate * (p.sessions - 1)) + 100) / p.sessions
            if source: p.top_source = source

    def get_top_pages(self, top_k: int = 5) -> List[WebsiteAnalyticsData]:
        return sorted(self._pages.values(), key=lambda p: p.views, reverse=True)[:top_k]

    def get_page_stats(self, article_id: str) -> Optional[WebsiteAnalyticsData]:
        return self._pages.get(article_id)

    def get_summary(self) -> Dict[str, Any]:
        pages = list(self._pages.values())
        return {"total_articles": len(pages), "total_views": sum(p.views for p in pages),
                "total_sessions": sum(p.sessions for p in pages),
                "avg_bounce_rate": round(sum(p.bounce_rate for p in pages) / max(len(pages), 1), 1)}

    def get_stats(self) -> Dict:
        s = self.get_summary(); return {"total_tracked": s["total_articles"], "total_views": s["total_views"]}
