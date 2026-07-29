"""LandingPageManager — Track top/worst landing pages, exit pages, bounce pages."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.traffic_manager.models.traffic_models import LandingPage


class LandingPageManager:
    """Analyze landing page performance — top pages, bounce rates, exits."""

    def __init__(self) -> None:
        self._pages: Dict[str, LandingPage] = {}
        self._lock = threading.Lock()

    def record_page(self, url: str, article_id: str = "", title: str = "",
                     sessions: int = 1, pageviews: int = 1,
                     bounce: bool = False, duration: float = 0.0) -> LandingPage:
        with self._lock:
            if url not in self._pages:
                self._pages[url] = LandingPage(url=url, article_id=article_id, title=title)
            page = self._pages[url]
            page.sessions += 1
            page.pageviews += pageviews
            if bounce: page.bounce_rate = ((page.bounce_rate * (page.sessions - 1)) + 100) / page.sessions
            page.avg_duration = ((page.avg_duration * (page.sessions - 1)) + duration) / page.sessions
            page.exits += 1 if bounce else 0
        return self._pages[url]

    def get_top_pages(self, top_k: int = 5) -> List[LandingPage]:
        return sorted(self._pages.values(), key=lambda p: p.sessions, reverse=True)[:top_k]

    def get_worst_pages(self, top_k: int = 5) -> List[LandingPage]:
        return sorted(self._pages.values(), key=lambda p: p.bounce_rate, reverse=True)[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        pages = list(self._pages.values())
        avg_bounce = sum(p.bounce_rate for p in pages) / max(len(pages), 1)
        return {"total_pages": len(pages), "avg_bounce_rate": round(avg_bounce, 1),
                "total_sessions": sum(p.sessions for p in pages)}
