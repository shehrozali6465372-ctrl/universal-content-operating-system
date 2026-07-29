"""SEOAnalytics — Track SEO scores, keyword rankings, organic traffic, indexed pages."""
from __future__ import annotations
import time
import random
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.models.seo_models import SEOAnalytics as SEOAnalyticsModel


class SEOAnalytics:
    """Track and report SEO performance metrics."""

    def __init__(self) -> None:
        self._records: Dict[str, List[SEOAnalyticsModel]] = {}
        self._report_log: List[dict] = []

    def record(self, article_id: str, google_impressions: int = 0,
                google_clicks: int = 0, google_ctr: float = 0.0,
                google_avg_position: float = 0.0,
                pinterest_impressions: int = 0, pinterest_clicks: int = 0,
                pinterest_saves: int = 0,
                is_indexed: bool = False, seo_score: float = 0.0) -> SEOAnalyticsModel:
        """Record SEO analytics for an article."""
        analytics = SEOAnalyticsModel(
            article_id=article_id,
            google_impressions=google_impressions,
            google_clicks=google_clicks,
            google_ctr=google_ctr or (google_clicks / max(google_impressions, 1)) * 100,
            google_avg_position=google_avg_position,
            pinterest_impressions=pinterest_impressions,
            pinterest_clicks=pinterest_clicks,
            pinterest_saves=pinterest_saves,
            is_indexed=is_indexed,
            seo_score=seo_score,
        )

        if article_id not in self._records:
            self._records[article_id] = []
        self._records[article_id].append(analytics)
        return analytics

    def simulate_analytics(self, article_id: str, seo_score: float = 70.0) -> SEOAnalyticsModel:
        """Simulate SEO analytics data (for testing)."""
        multiplier = seo_score / 100.0
        return self.record(
            article_id=article_id,
            google_impressions=int(random.randint(100, 5000) * multiplier),
            google_clicks=int(random.randint(5, 200) * multiplier),
            google_avg_position=random.uniform(3.0, 20.0),
            pinterest_impressions=int(random.randint(200, 10000) * multiplier),
            pinterest_clicks=int(random.randint(10, 500) * multiplier),
            pinterest_saves=int(random.randint(5, 200) * multiplier),
            is_indexed=seo_score >= 50,
            seo_score=seo_score,
        )

    def get_article_performance(self, article_id: str) -> Dict[str, Any]:
        records = self._records.get(article_id, [])
        if not records:
            return {"error": "No data"}
        latest = records[-1]
        total_impressions = sum(r.google_impressions + r.pinterest_impressions for r in records)
        total_clicks = sum(r.google_clicks + r.pinterest_clicks for r in records)
        return {
            "article_id": article_id,
            "latest": latest.to_dict(),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_traffic": sum(r.total_traffic for r in records),
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate SEO performance report."""
        total_impressions = 0
        total_clicks = 0
        indexed = 0
        total_articles = len(self._records)

        for records in self._records.values():
            latest = records[-1] if records else None
            if latest:
                total_impressions += latest.google_impressions + latest.pinterest_impressions
                total_clicks += latest.google_clicks + latest.pinterest_clicks
                if latest.is_indexed:
                    indexed += 1

        report = {
            "total_articles_tracked": total_articles,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "indexed_pages": indexed,
            "indexation_rate": round((indexed / max(total_articles, 1)) * 100, 1),
            "avg_ctr": round((total_clicks / max(total_impressions, 1)) * 100, 2),
        }

        self._report_log.append(report)
        return report

    def get_stats(self) -> Dict[str, Any]:
        return {"total_records": sum(len(r) for r in self._records.values()), "total_reports": len(self._report_log)}
