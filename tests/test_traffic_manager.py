"""Comprehensive tests for Layer 23 — Module 8: Traffic Manager."""
from __future__ import annotations
import time
import pytest
from layers.layer23_website_manager.traffic_manager.traffic_manager import TrafficManager, get_traffic_manager
from layers.layer23_website_manager.traffic_manager.models.traffic_models import (
    TrafficSource, Visitor, TrafficAnalytics, LandingPage, Campaign, Alert,
    TrafficForecast, TrafficSourceType, AlertSeverity, CampaignStatus,
)
from layers.layer23_website_manager.traffic_manager.exceptions import (
    TrafficTrackingError, SourceNotFoundError, AttributionError, ForecastError,
    CampaignError, AlertError, TrafficHealthError, VisitorTrackingError, DashboardError,
)


class TestTrafficSource:
    def test_default(self):
        s = TrafficSource()
        assert s.source_id is not None
        assert s.source_type == TrafficSourceType.OTHER
    def test_with_values(self):
        s = TrafficSource(source_type=TrafficSourceType.PINTEREST, article_id="a1", pin_id="p1")
        assert s.source_type == TrafficSourceType.PINTEREST
    def test_to_dict(self):
        s = TrafficSource(source_type=TrafficSourceType.GOOGLE_ORGANIC)
        assert "source" in s.to_dict()


class TestVisitor:
    def test_default(self):
        v = Visitor()
        assert v.is_new is True
        assert v.page_views == 1
    def test_session(self):
        v = Visitor(session_duration=120.5, device="mobile")
        assert v.device == "mobile"
    def test_to_dict(self):
        v = Visitor(device="tablet")
        assert "device" in v.to_dict()


class TestTrafficAnalytics:
    def test_default(self):
        a = TrafficAnalytics()
        assert a.sessions == 0
    def test_pinterest(self):
        a = TrafficAnalytics(pinterest_clicks=100, pinterest_saves=20)
        assert a.pinterest_clicks == 100


class TestLandingPage:
    def test_default(self):
        p = LandingPage(url="/test")
        assert p.sessions == 0
    def test_to_dict(self):
        p = LandingPage(url="/test", title="Test Page")
        d = p.to_dict()
        assert d["url"] == "/test"


class TestCampaign:
    def test_default(self):
        c = Campaign()
        assert c.status == CampaignStatus.DRAFT
    def test_metrics(self):
        c = Campaign(clicks=100, impressions=1000)
        assert c.ctr == 10.0
    def test_conversion_rate(self):
        c = Campaign(clicks=100, conversions=5)
        assert c.conversion_rate == 5.0
    def test_roi(self):
        c = Campaign(spent=100, conversions=20)
        assert c.roi > 0


class TestAlert:
    def test_default(self):
        a = Alert()
        assert a.severity == AlertSeverity.INFO
        assert a.is_read is False
    def test_to_dict(self):
        a = Alert(title="Test", severity=AlertSeverity.CRITICAL)
        d = a.to_dict()
        assert d["severity"] == "critical"


class TestTrafficForecast:
    def test_default(self):
        f = TrafficForecast()
        assert f.period == "daily"
        assert f.confidence == 0.0


class TestTrafficSourceManager:
    def setup_method(self): self.tm = TrafficManager()
    def test_record_source(self):
        s = self.tm.sources.record_source(TrafficSourceType.PINTEREST, article_id="a1")
        assert s.source_type == TrafficSourceType.PINTEREST
    def test_get_sources(self):
        self.tm.sources.record_source(TrafficSourceType.GOOGLE_ORGANIC)
        assert len(self.tm.sources.get_sources(30)) >= 1
    def test_traffic_breakdown(self):
        self.tm.sources.record_source(TrafficSourceType.PINTEREST)
        breakdown = self.tm.get_traffic_breakdown()
        assert len(breakdown) > 0
    def test_simulate_traffic(self):
        count = self.tm.sources.simulate_traffic("a1", "p1", total_visits=50)
        assert count == 50
    def test_source_stats(self):
        self.tm.sources.record_source(TrafficSourceType.DIRECT)
        stats = self.tm.sources.get_stats()
        assert stats["total_sources"] >= 1


class TestVisitorTracker:
    def setup_method(self): self.tm = TrafficManager()
    def test_record_visit(self):
        v = self.tm.visitors.record_visit(is_new=True, device="mobile")
        assert v.is_new is True
    def test_visitor_count(self):
        self.tm.visitors.record_visit(is_new=True)
        self.tm.visitors.record_visit(is_new=False)
        stats = self.tm.visitors.get_visitor_count(30)
        assert stats["total"] >= 2
    def test_simulate_visitors(self):
        count = self.tm.visitors.simulate_visitors(20)
        assert count == 20
    def test_visitor_stats(self):
        self.tm.visitors.record_visit()
        stats = self.tm.visitors.get_stats()
        assert stats["total_visits"] >= 1


class TestAttributionEngine:
    def setup_method(self): self.tm = TrafficManager()
    def test_attribution_pinterest(self):
        r = self.tm.attribution.attribute_traffic("pinterest", "a1", "p1", "b1", "acc1")
        assert r["source"] == "pinterest"
        assert r["confidence"] >= 0.8
    def test_attribution_google(self):
        r = self.tm.attribution.attribute_traffic("google_organic", "a1")
        assert "Google" in r["attribution_path"]
    def test_attribution_stats(self):
        self.tm.attribution.attribute_traffic("direct", "a1")
        stats = self.tm.attribution.get_stats()
        assert stats["total_attributions"] >= 1


class TestLandingPageManager:
    def setup_method(self): self.tm = TrafficManager()
    def test_record_page(self):
        p = self.tm.landing_pages.record_page("/test", title="Test", sessions=1)
        assert p.url == "/test"
    def test_top_pages(self):
        self.tm.landing_pages.record_page("/a", title="A", sessions=10)
        self.tm.landing_pages.record_page("/b", title="B", sessions=5)
        top = self.tm.get_top_pages(1)
        assert len(top) == 1
    def test_worst_pages(self):
        self.tm.landing_pages.record_page("/bad", title="Bad", sessions=1, bounce=True)
        worst = self.tm.landing_pages.get_worst_pages(1)
        assert len(worst) == 1
    def test_landing_stats(self):
        self.tm.landing_pages.record_page("/stats", sessions=5)
        stats = self.tm.landing_pages.get_stats()
        assert stats["total_pages"] >= 1


class TestPinterestTrafficTracker:
    def setup_method(self): self.tm = TrafficManager()
    def test_record_click(self):
        self.tm.pinterest.record_pin_click("p1", "b1", "a1")
        assert self.tm.pinterest.get_pin_traffic("p1")["clicks"] == 1
    def test_record_save(self):
        self.tm.pinterest.record_save("p1")
        assert self.tm.pinterest.get_pin_traffic("p1")["saves"] == 1
    def test_top_pins(self):
        self.tm.pinterest.record_pin_click("p1", "b1")
        self.tm.pinterest.record_pin_click("p2", "b2")
        self.tm.pinterest.record_pin_click("p1", "b1")
        top = self.tm.pinterest.get_top_pins(2)
        assert len(top) == 2
    def test_simulate_activity(self):
        count = self.tm.pinterest.simulate_activity(pin_count=3, days=2)
        assert count > 0
    def test_pinterest_stats(self):
        self.tm.pinterest.record_pin_click("p1")
        stats = self.tm.pinterest.get_stats()
        assert stats["total_pin_clicks"] >= 1


class TestSearchTrafficManager:
    def setup_method(self): self.tm = TrafficManager()
    def test_record_keyword(self):
        self.tm.search.record_keyword("bedroom ideas", position=5, clicks=50, impressions=1000)
        stats = self.tm.search.get_keyword_stats("bedroom ideas")
        assert stats["clicks"] == 50
    def test_top_keywords(self):
        self.tm.search.record_keyword("kw1", clicks=100)
        self.tm.search.record_keyword("kw2", clicks=50)
        top = self.tm.get_top_keywords(2)
        assert len(top) == 2
    def test_simulate_search(self):
        count = self.tm.search.simulate_search(3)
        assert count == 3
    def test_search_stats(self):
        self.tm.search.record_keyword("test kw")
        stats = self.tm.search.get_stats()
        assert stats["total_keywords"] >= 1


class TestBehaviorAnalyzer:
    def setup_method(self): self.tm = TrafficManager()
    def test_record_behavior(self):
        self.tm.behavior.record_behavior("a1", scroll_depth=50, time_on_page=120)
        behavior = self.tm.get_article_behavior("a1")
        assert behavior["sessions"] >= 1
    def test_simulate_behavior(self):
        count = self.tm.behavior.simulate_behavior(2, 10)
        assert count == 10
    def test_behavior_stats(self):
        self.tm.behavior.record_behavior("a1")
        stats = self.tm.behavior.get_stats()
        assert stats["total_records"] >= 1


class TestTrafficOptimizer:
    def setup_method(self): self.tm = TrafficManager()
    def test_analyze_traffic(self):
        result = self.tm.analyze_traffic_sources()
        assert "suggestions" in result
    def test_optimizer_stats(self):
        self.tm.analyze_traffic_sources()
        stats = self.tm.optimizer.get_stats()
        assert stats["total_analyses"] >= 1


class TestTrafficHealthChecker:
    def setup_method(self): self.tm = TrafficManager()
    def test_healthy(self):
        result = self.tm.health.check_health(100, 80, bounce_rate=30, ctr=3.0, indexed_pages=50)
        assert result["status"] == "healthy"
    def test_critical_drop(self):
        result = self.tm.health.check_health(30, 100, bounce_rate=80, ctr=0.5)
        assert result["status"] == "critical"
    def test_health_stats(self):
        self.tm.health.check_health(50, 40)
        stats = self.tm.health.get_stats()
        assert stats["total_checks"] >= 1


class TestForecastEngine:
    def setup_method(self): self.tm = TrafficManager()
    def test_forecast_daily(self):
        f = self.tm.forecast.forecast(100, 0.05, days_ahead=1)
        assert f.predicted_visitors > 0
        assert f.confidence > 0
    def test_forecast_weekly(self):
        f = self.tm.forecast.forecast(100, days_ahead=7)
        assert f.predicted_visitors >= 700

class TestCampaignManager:
    def setup_method(self): self.tm = TrafficManager()
    def test_create_campaign(self):
        c = self.tm.create_campaign("Summer Sale", "seasonal", "fashion", 500)
        assert c.name == "Summer Sale"
        assert c.status == CampaignStatus.DRAFT
    def test_start_campaign(self):
        c = self.tm.create_campaign("Start Test")
        assert self.tm.campaigns.start_campaign(c.campaign_id) is True
        assert c.status == CampaignStatus.ACTIVE
    def test_pause_campaign(self):
        c = self.tm.create_campaign("Pause Test")
        self.tm.campaigns.start_campaign(c.campaign_id)
        assert self.tm.campaigns.pause_campaign(c.campaign_id) is True
    def test_record_metric(self):
        c = self.tm.create_campaign("Metric Test")
        self.tm.campaigns.start_campaign(c.campaign_id)
        self.tm.campaigns.record_metric(c.campaign_id, clicks=100, impressions=1000, conversions=5, spent=50)
        assert c.clicks == 100
    def test_active_campaigns(self):
        c = self.tm.create_campaign("Active Test")
        self.tm.campaigns.start_campaign(c.campaign_id)
        assert len(self.tm.get_active_campaigns()) >= 1
    def test_campaign_stats(self):
        self.tm.create_campaign("Stats")
        stats = self.tm.campaigns.get_stats()
        assert stats["total_campaigns"] >= 1


class TestAlertManager:
    def setup_method(self): self.tm = TrafficManager()
    def test_create_alert(self):
        a = self.tm.alerts.create_alert(AlertSeverity.WARNING, "Test Alert", "Test message")
        assert a.severity == AlertSeverity.WARNING
    def test_unread_alerts(self):
        self.tm.alerts.create_alert(AlertSeverity.INFO, "Info", "Test")
        assert len(self.tm.get_unread_alerts()) >= 1
    def test_mark_read(self):
        a = self.tm.alerts.create_alert(AlertSeverity.INFO, "Read", "Test")
        assert self.tm.alerts.mark_read(a.alert_id) is True
        assert a.is_read is True
    def test_mark_all_read(self):
        self.tm.alerts.create_alert(AlertSeverity.INFO, "A1", "T1")
        self.tm.alerts.create_alert(AlertSeverity.WARNING, "A2", "T2")
        count = self.tm.alerts.mark_all_read()
        assert count >= 1
    def test_traffic_anomaly_spike(self):
        alert = self.tm.alerts.check_traffic_anomaly(200, 50, "a1")
        assert alert is not None
        assert "spike" in alert.title.lower()
    def test_traffic_anomaly_drop(self):
        alert = self.tm.alerts.check_traffic_anomaly(10, 100, "a1")
        assert alert is not None
        assert "drop" in alert.title.lower()
    def test_alert_stats(self):
        self.tm.alerts.create_alert(AlertSeverity.CRITICAL, "Critical", "Test")
        stats = self.tm.alerts.get_stats()
        assert stats["total_alerts"] >= 1


class TestTrafficDashboard:
    def setup_method(self): self.tm = TrafficManager()
    def test_generate_dashboard(self):
        self.tm.simulate_traffic(days=1, articles=2, pins=3)
        dash = self.tm.get_dashboard()
        assert "live" in dash
        assert "content" in dash
        assert "health" in dash


class TestTrafficManagerFacade:
    def setup_method(self): self.tm = TrafficManager()
    def test_record_visit(self):
        r = self.tm.record_visit("pinterest", "a1", "p1", "b1")
        assert "source_id" in r
        assert "attribution" in r
    def test_simulate_traffic(self):
        r = self.tm.simulate_traffic(days=2)
        assert r["sources_recorded"] > 0
    def test_get_status(self):
        status = self.tm.get_status()
        assert status["module"] == "Traffic Manager (Layer 23 / Module 8)"
        assert "sources" in status
        assert "visitors" in status
        assert "pinterest" in status
        assert "search" in status
        assert "campaigns" in status
        assert "alerts" in status
    def test_check_health(self):
        self.tm.simulate_traffic(days=1)
        health = self.tm.check_traffic_health()
        assert "health_score" in health
    def test_forecast(self):
        self.tm.simulate_traffic(days=1)
        f = self.tm.forecast_traffic(7)
        assert f.predicted_visitors > 0
    def test_get_dashboard(self):
        self.tm.simulate_traffic(days=1)
        dash = self.tm.get_dashboard()
        assert "live" in dash


class TestSingleton:
    def test_get_traffic_manager(self):
        t1 = get_traffic_manager(); t2 = get_traffic_manager()
        assert t1 is t2


class TestExceptions:
    def test_all_importable(self):
        assert issubclass(TrafficTrackingError, Exception)
        assert issubclass(SourceNotFoundError, Exception)
        assert issubclass(AttributionError, Exception)
        assert issubclass(ForecastError, Exception)
        assert issubclass(CampaignError, Exception)
        assert issubclass(AlertError, Exception)
        assert issubclass(TrafficHealthError, Exception)
        assert issubclass(VisitorTrackingError, Exception)
        assert issubclass(DashboardError, Exception)
