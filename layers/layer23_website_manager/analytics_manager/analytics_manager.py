"""AnalyticsManager — Layer 23 / Module 9.

Central Analytics Intelligence Hub. Collects data from all Pinterest Business Platform
modules and provides actionable insights, KPIs, reports, and dashboards.
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.analytics_manager.models.analytics_models import (
    AnalyticsSummary, AnalyticsReport, KPI, AIInsight, TrendData, KPICategory, InsightType,
)
from layers.layer23_website_manager.analytics_manager.website.website_analytics import WebsiteAnalytics
from layers.layer23_website_manager.analytics_manager.pinterest.pinterest_analytics import PinterestAnalytics
from layers.layer23_website_manager.analytics_manager.seo.seo_analytics import SEOAnalytics
from layers.layer23_website_manager.analytics_manager.affiliate.affiliate_analytics import AffiliateAnalytics
from layers.layer23_website_manager.analytics_manager.content.content_analytics import ContentAnalytics
from layers.layer23_website_manager.analytics_manager.campaigns.campaign_analytics import CampaignAnalytics
from layers.layer23_website_manager.analytics_manager.kpi.kpi_manager import KPIManager
from layers.layer23_website_manager.analytics_manager.insights.ai_insights_engine import AIInsightsEngine
from layers.layer23_website_manager.analytics_manager.trends.trend_analyzer import TrendAnalyzer
from layers.layer23_website_manager.analytics_manager.reports.report_generator import ReportGenerator
from layers.layer23_website_manager.analytics_manager.dashboard.dashboard_manager import DashboardManager
from layers.layer23_website_manager.analytics_manager.export.export_manager import ExportManager
from layers.layer23_website_manager.analytics_manager.api.analytics_api import AnalyticsAPI


class AnalyticsManager:
    """Primary facade for Analytics Manager. Coordinates 13 sub-modules."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()

        self.website = WebsiteAnalytics()
        self.pinterest = PinterestAnalytics()
        self.seo = SEOAnalytics()
        self.affiliate = AffiliateAnalytics()
        self.content = ContentAnalytics()
        self.campaigns = CampaignAnalytics()
        self.kpi = KPIManager()
        self.insights = AIInsightsEngine()
        self.trends = TrendAnalyzer()
        self.reports = ReportGenerator()
        self.dashboard_mgr = DashboardManager()
        self.export = ExportManager()
        self.api = AnalyticsAPI(self)
        self._total_operations = 0

    # ─── Recording ────────────────────────────────────────

    def record_page_view(self, article_id: str, title: str = "",
                          duration: float = 0.0, bounced: bool = False, source: str = ""):
        self.website.record_page_view(article_id, title, duration, bounced, source)
        self._log("record_page_view", {})

    def record_pin_performance(self, pin_id: str, board_id: str = "", account_id: str = "",
                                impressions: int = 0, saves: int = 0, clicks: int = 0):
        self.pinterest.record_pin_performance(pin_id, board_id, account_id, impressions, saves, clicks)
        self._log("record_pin", {})

    def record_seo_keyword(self, keyword: str, article_id: str = "", position: float = 10.0,
                            impressions: int = 100, clicks: int = 1):
        self.seo.record_keyword(keyword, article_id, position, impressions, clicks)
        self._log("record_keyword", {})

    def record_affiliate_product(self, product_id: str, product_name: str = "",
                                  clicks: int = 0, sales: int = 0,
                                  commission: float = 0.0, revenue: float = 0.0):
        self.affiliate.record_product(product_id, product_name, clicks, sales, commission, revenue)
        self._log("record_affiliate", {})

    def record_article_content(self, article_id: str, title: str = "",
                                views: int = 0, pins: int = 0, clicks: int = 0, revenue: float = 0.0):
        self.content.record_article(article_id, title, views, pins, clicks, revenue)
        self._log("record_content", {})

    def record_campaign(self, campaign_id: str, name: str = "", impressions: int = 0,
                         clicks: int = 0, conversions: int = 0, spent: float = 0.0, revenue: float = 0.0):
        self.campaigns.record_campaign(campaign_id, name, impressions, clicks, conversions, spent, revenue)
        self._log("record_campaign", {})

    # ─── KPI Calculation ──────────────────────────────────

    def calculate_kpis(self) -> List[KPI]:
        ws = self.website.get_summary()
        ps = self.pinterest.get_summary()
        ss = self.seo.get_summary()
        af = self.affiliate.get_summary()
        cs = self.content.get_summary()

        kpis = [
            self.kpi.calculate_kpi("Website Views", KPICategory.TRAFFIC, ws.get("total_views", 0), unit="views"),
            self.kpi.calculate_kpi("Pinterest Clicks", KPICategory.TRAFFIC, ps.get("total_clicks", 0), unit="clicks"),
            self.kpi.calculate_kpi("Organic Clicks", KPICategory.SEO, ss.get("total_clicks", 0), unit="clicks"),
            self.kpi.calculate_kpi("Affiliate Revenue", KPICategory.REVENUE, af.get("total_revenue", 0), unit="$"),
            self.kpi.calculate_kpi("Conversion Rate", KPICategory.REVENUE, af.get("conversion_rate", 0), unit="%"),
            self.kpi.calculate_kpi("Articles Published", KPICategory.CONTENT, cs.get("total_articles", 0), unit="count"),
            self.kpi.calculate_kpi("Avg Position", KPICategory.SEO, ss.get("avg_position", 0), unit="pos"),
            self.kpi.calculate_kpi("Bounce Rate", KPICategory.ENGAGEMENT, ws.get("avg_bounce_rate", 0), unit="%"),
        ]
        return kpis

    # ─── Insights & Trends ────────────────────────────────

    def generate_insights(self, traffic_breakdown: Optional[Dict[str, int]] = None) -> List[AIInsight]:
        return self.insights.generate_insights(
            traffic_breakdown=traffic_breakdown or {},
            affiliate_summary=self.affiliate.get_summary(),
            content_summary=self.content.get_summary(),
        )

    def detect_trend(self, category: str, item: str, current: float, previous: float) -> TrendData:
        return self.trends.detect_trend(category, item, current, previous)

    # ─── Reports ──────────────────────────────────────────

    def generate_daily_report(self) -> AnalyticsReport:
        data = {**self.website.get_summary(), **self.pinterest.get_summary(),
                **self.seo.get_summary(), **self.affiliate.get_summary(),
                **self.content.get_summary()}
        return self.reports.generate_daily_report(data)

    def generate_weekly_report(self) -> AnalyticsReport:
        data = self.api.get_summary()
        return self.reports.generate_weekly_report(data)

    def generate_monthly_report(self) -> AnalyticsReport:
        data = {**self.api.get_summary(), "top_performers": self.api.get_top_performers()}
        return self.reports.generate_monthly_report(data)

    def generate_executive_report(self) -> AnalyticsReport:
        kpis = self.calculate_kpis()
        insights = self.generate_insights()
        trends = self.trends.get_rising_trends()
        return self.reports.generate_executive_report(kpis, insights, trends)

    # ─── Dashboard ────────────────────────────────────────

    def get_dashboard(self) -> Dict[str, Any]:
        summary = self.api.get_summary()
        kpis = self.calculate_kpis()
        top_pins = self.pinterest.get_top_pins(5)
        top_articles = self.content.get_best_articles(5)
        insights = self.generate_insights()
        return self.dashboard_mgr.generate_dashboard(summary, kpis, top_pins, top_articles, insights)

    # ─── Export ───────────────────────────────────────────

    def export_dashboard_json(self) -> str:
        return self.export.export_json(self.get_dashboard())

    def export_kpis_csv(self) -> str:
        kpis = self.calculate_kpis()
        headers = ["Name", "Value", "Unit", "Change %", "Trend"]
        rows = [[k.name, k.value, k.unit, k.change_pct, k.trend] for k in kpis]
        return self.export.export_csv(headers, rows)

    # ─── Simulation ───────────────────────────────────────

    def simulate_analytics(self) -> Dict[str, Any]:
        import random
        for i in range(5):
            self.record_page_view(f"art_{i}", f"Article {i}", random.uniform(30, 300),
                                   bounced=random.random() < 0.3, source=random.choice(["pinterest", "google", "direct"]))
            self.record_pin_performance(f"pin_{i}", f"board_{i%3}", f"acc_{i%2+1}",
                                         random.randint(100, 5000), random.randint(5, 200), random.randint(10, 300))
            self.record_affiliate_product(f"prod_{i}", f"Product {i}",
                                           random.randint(10, 500), random.randint(1, 20),
                                           random.uniform(5, 100), random.uniform(10, 200))
            self.record_article_content(f"art_{i}", f"Article {i}", random.randint(50, 2000))
        for i in range(3):
            self.record_seo_keyword(f"keyword_{i}", f"art_{i}", random.uniform(1, 15),
                                     random.randint(100, 3000), random.randint(5, 150))
        return {"simulated": True}

    # ─── Status ───────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return {
            "module": "Analytics Manager (Layer 23 / Module 9)",
            "version": "1.0.0", "overall": "Healthy",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "website": self.website.get_stats(),
            "pinterest": self.pinterest.get_stats(),
            "seo": self.seo.get_stats(),
            "affiliate": self.affiliate.get_stats(),
            "content": self.content.get_stats(),
            "campaigns": self.campaigns.get_stats(),
            "kpi": self.kpi.get_stats(),
            "insights": self.insights.get_stats(),
            "trends": self.trends.get_stats(),
            "reports": self.reports.get_stats(),
            "export": self.export.get_stats(),
            "operations": {"total": self._total_operations},
        }

    def _log(self, operation: str, details: dict) -> None:
        with self._lock: self._total_operations += 1


_analytics_manager_instance = None
_instance_lock = threading.Lock()


def get_analytics_manager():
    global _analytics_manager_instance
    if _analytics_manager_instance is None:
        with _instance_lock:
            if _analytics_manager_instance is None:
                _analytics_manager_instance = AnalyticsManager()
    return _analytics_manager_instance
