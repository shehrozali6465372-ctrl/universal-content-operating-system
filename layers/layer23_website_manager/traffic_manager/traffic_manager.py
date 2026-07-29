"""TrafficManager — Layer 23 / Module 8.

Traffic Intelligence Engine: monitor, analyze, and optimize all traffic sources.
Flow: Traffic → Sources → Visitors → Attribution → Analysis → Optimization → Dashboard
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.traffic_manager.models.traffic_models import (
    TrafficSource, Visitor, TrafficAnalytics, LandingPage, Campaign, Alert,
    TrafficForecast, TrafficSourceType, AlertSeverity, CampaignStatus,
)
from layers.layer23_website_manager.traffic_manager.sources.traffic_source_manager import TrafficSourceManager
from layers.layer23_website_manager.traffic_manager.visitors.visitor_tracker import VisitorTracker
from layers.layer23_website_manager.traffic_manager.attribution.attribution_engine import AttributionEngine
from layers.layer23_website_manager.traffic_manager.landing_pages.landing_page_manager import LandingPageManager
from layers.layer23_website_manager.traffic_manager.pinterest.pinterest_traffic_tracker import PinterestTrafficTracker
from layers.layer23_website_manager.traffic_manager.search.search_traffic_manager import SearchTrafficManager
from layers.layer23_website_manager.traffic_manager.behavior.behavior_analyzer import BehaviorAnalyzer
from layers.layer23_website_manager.traffic_manager.optimizer.traffic_optimizer import TrafficOptimizer
from layers.layer23_website_manager.traffic_manager.health.traffic_health_checker import TrafficHealthChecker
from layers.layer23_website_manager.traffic_manager.forecasting.forecast_engine import ForecastEngine
from layers.layer23_website_manager.traffic_manager.campaigns.campaign_manager import CampaignManager
from layers.layer23_website_manager.traffic_manager.alerts.alert_manager import AlertManager
from layers.layer23_website_manager.traffic_manager.dashboard.traffic_dashboard import TrafficDashboard


class TrafficManager:
    """Primary facade for Traffic Manager. Coordinates 13 sub-modules."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()

        self.sources = TrafficSourceManager()
        self.visitors = VisitorTracker()
        self.attribution = AttributionEngine()
        self.landing_pages = LandingPageManager()
        self.pinterest = PinterestTrafficTracker()
        self.search = SearchTrafficManager()
        self.behavior = BehaviorAnalyzer()
        self.optimizer = TrafficOptimizer()
        self.health = TrafficHealthChecker()
        self.forecast = ForecastEngine()
        self.campaigns = CampaignManager()
        self.alerts = AlertManager()
        self.dashboard = TrafficDashboard()
        self._total_operations = 0

    # ─── Traffic Recording ────────────────────────────────

    def record_visit(self, source_type: str, article_id: str = "",
                      pin_id: str = "", board_id: str = "",
                      device: str = "desktop", country: str = "",
                      is_new: bool = True) -> Dict[str, Any]:
        st = self._parse_source(source_type)
        source = self.sources.record_source(st, article_id=article_id, pin_id=pin_id,
                                              board_id=board_id, device=device, country=country)
        visitor = self.visitors.record_visit(is_new=is_new, device=device, country=country)
        attr = self.attribution.attribute_traffic(source_type, article_id, pin_id, board_id)
        self._log("record_visit", {"source": source_type})
        return {"source_id": source.source_id, "visitor_id": visitor.visitor_id, "attribution": attr}

    def _parse_source(self, source: str) -> TrafficSourceType:
        mapping = {"pinterest": TrafficSourceType.PINTEREST, "google": TrafficSourceType.GOOGLE_ORGANIC,
                    "google_discover": TrafficSourceType.GOOGLE_DISCOVER, "bing": TrafficSourceType.BING,
                    "direct": TrafficSourceType.DIRECT, "referral": TrafficSourceType.REFERRAL,
                    "social": TrafficSourceType.SOCIAL, "email": TrafficSourceType.EMAIL}
        return mapping.get(source.lower(), TrafficSourceType.OTHER)

    # ─── Analytics ────────────────────────────────────────

    def get_traffic_breakdown(self, days: int = 30) -> Dict[str, int]:
        return self.sources.get_traffic_breakdown(days)

    def get_visitor_stats(self, days: int = 30) -> Dict[str, int]:
        return self.visitors.get_visitor_count(days)

    def get_pin_traffic(self, pin_id: str) -> Dict[str, int]:
        return self.pinterest.get_pin_traffic(pin_id)

    def get_top_pins(self, top_k: int = 5) -> List[tuple]:
        return self.pinterest.get_top_pins(top_k)

    def get_top_pages(self, top_k: int = 5) -> List[LandingPage]:
        return self.landing_pages.get_top_pages(top_k)

    def get_top_keywords(self, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.search.get_top_keywords(top_k)

    def get_article_behavior(self, article_id: str) -> Dict[str, Any]:
        return self.behavior.get_article_behavior(article_id)

    # ─── Simulation ───────────────────────────────────────

    def simulate_traffic(self, days: int = 7, articles: int = 3, pins: int = 5) -> Dict[str, Any]:
        """Simulate realistic traffic for testing."""
        visits = self.sources.simulate_traffic("art_0", "pin_0", "board_0", total_visits=days * 20)
        vis = self.visitors.simulate_visitors(days * 10)
        search = self.search.simulate_search(5)
        beh = self.behavior.simulate_behavior(articles, days * 5)
        p_act = self.pinterest.simulate_activity(pins, days)
        return {"sources_recorded": visits, "visitors_recorded": vis,
                "keywords_recorded": search, "behaviors_recorded": beh,
                "pinterest_activities": p_act}

    # ─── Optimization & Health ────────────────────────────

    def analyze_traffic_sources(self) -> Dict[str, Any]:
        breakdown = self.get_traffic_breakdown()
        top_pages = self.landing_pages.get_top_pages(3)
        top_pins = self.pinterest.get_top_pins(3)
        return self.optimizer.analyze_traffic(breakdown, top_pages, top_pins)

    def check_traffic_health(self) -> Dict[str, Any]:
        stats = self.sources.get_stats()
        vis = self.visitors.get_visitor_count()
        return self.health.check_health(stats["total_sources"], max(stats["total_sources"] - 10, 0))

    def forecast_traffic(self, days_ahead: int = 7) -> TrafficForecast:
        stats = self.sources.get_stats()
        daily_avg = stats["total_sources"] / max((time.time() - self._start_time) / 86400, 1)
        return self.forecast.forecast(daily_avg, days_ahead=days_ahead)

    # ─── Campaigns & Alerts ───────────────────────────────

    def create_campaign(self, name: str, campaign_type: str = "seasonal",
                         niche: str = "", budget: float = 0.0) -> Campaign:
        return self.campaigns.create_campaign(name, campaign_type, niche=niche, budget=budget)

    def get_active_campaigns(self) -> List[Campaign]:
        return self.campaigns.get_active_campaigns()

    def get_unread_alerts(self) -> List[Alert]:
        return self.alerts.get_unread_alerts()

    def check_traffic_anomaly(self, current: float, previous: float,
                                article_id: str = "") -> Optional[Alert]:
        return self.alerts.check_traffic_anomaly(current, previous, article_id)

    # ─── Dashboard ────────────────────────────────────────

    def get_dashboard(self) -> Dict[str, Any]:
        breakdown = self.get_traffic_breakdown()
        top_pages = self.landing_pages.get_top_pages(5)
        top_pins = self.pinterest.get_top_pins(5)
        total_articles = len(set(s.article_id for s in self.sources._sources if s.article_id))
        health = self.health.check_health(self.sources.get_stats()["total_sources"],
                                           max(self.sources.get_stats()["total_sources"] - 5, 0))
        return self.dashboard.generate(
            self.visitors.get_visitor_count()["total"], breakdown,
            top_pages, top_pins, total_articles, health["health_score"],
        )

    # ─── Status ───────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return {
            "module": "Traffic Manager (Layer 23 / Module 8)",
            "version": "1.0.0", "overall": "Healthy",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "sources": self.sources.get_stats(),
            "visitors": self.visitors.get_stats(),
            "attribution": self.attribution.get_stats(),
            "landing_pages": self.landing_pages.get_stats(),
            "pinterest": self.pinterest.get_stats(),
            "search": self.search.get_stats(),
            "behavior": self.behavior.get_stats(),
            "optimizer": self.optimizer.get_stats(),
            "health": self.health.get_stats(),
            "campaigns": self.campaigns.get_stats(),
            "alerts": self.alerts.get_stats(),
            "forecast": {"available": True},
            "operations": {"total": self._total_operations},
        }

    def _log(self, operation: str, details: dict) -> None:
        with self._lock: self._total_operations += 1


_traffic_manager_instance = None
_instance_lock = threading.Lock()


def get_traffic_manager():
    global _traffic_manager_instance
    if _traffic_manager_instance is None:
        with _instance_lock:
            if _traffic_manager_instance is None:
                _traffic_manager_instance = TrafficManager()
    return _traffic_manager_instance
