"""SEOAnalytics — Track organic clicks, search position, indexed pages, keywords, CTR."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.analytics_manager.models.analytics_models import SEOAnalyticsData


class SEOAnalytics:
    def __init__(self):
        self._keywords: Dict[str, SEOAnalyticsData] = {}
        self._articles: Dict[str, List[SEOAnalyticsData]] = {}
        self._lock = threading.Lock()
        self._indexed_pages = 0

    def record_keyword(self, keyword: str, article_id: str = "", position: float = 10.0,
                        impressions: int = 100, clicks: int = 1, is_indexed: bool = True):
        data = SEOAnalyticsData(article_id=article_id, keyword=keyword, position=position,
                                 impressions=impressions, clicks=clicks,
                                 ctr=(clicks / max(impressions, 1)) * 100, is_indexed=is_indexed)
        with self._lock:
            self._keywords[keyword] = data
            if article_id:
                if article_id not in self._articles: self._articles[article_id] = []
                self._articles[article_id].append(data)
            if is_indexed: self._indexed_pages += 1

    def get_top_keywords(self, top_k: int = 5) -> List[SEOAnalyticsData]:
        return sorted(self._keywords.values(), key=lambda k: k.clicks, reverse=True)[:top_k]

    def get_article_seo(self, article_id: str) -> List[SEOAnalyticsData]:
        return self._articles.get(article_id, [])

    def get_summary(self) -> Dict[str, Any]:
        kws = list(self._keywords.values())
        return {"total_keywords": len(kws), "total_clicks": sum(k.clicks for k in kws),
                "total_impressions": sum(k.impressions for k in kws),
                "avg_position": round(sum(k.position for k in kws) / max(len(kws), 1), 1),
                "indexed_pages": self._indexed_pages}

    def get_stats(self) -> Dict:
        s = self.get_summary(); return {"total_keywords": s["total_keywords"], "indexed_pages": s["indexed_pages"]}
