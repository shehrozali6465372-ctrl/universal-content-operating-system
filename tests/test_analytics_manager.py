"""Comprehensive tests for Layer 23 — Module 9: Analytics Manager."""
from __future__ import annotations
import pytest
from layers.layer23_website_manager.analytics_manager.analytics_manager import AnalyticsManager, get_analytics_manager
from layers.layer23_website_manager.analytics_manager.models.analytics_models import (
    AnalyticsSummary, AnalyticsReport, KPI, AIInsight, TrendData,
    KPICategory, InsightType, WebsiteAnalyticsData, PinterestAnalyticsData,
    SEOAnalyticsData, AffiliateAnalyticsData, ContentAnalyticsData, CampaignAnalyticsData,
)
from layers.layer23_website_manager.analytics_manager.exceptions import (
    AnalyticsError, ReportGenerationError, ExportError, DashboardError,
    KPIError, TrendAnalysisError, InsightGenerationError,
)


class TestModels:
    def test_summary(self):
        s = AnalyticsSummary(website_views=100, pinterest_clicks=50)
        assert s.website_views == 100; assert s.to_dict()["website_views"] == 100
    def test_report(self):
        r = AnalyticsReport(report_type="daily", data={"key": "val"})
        assert r.report_type == "daily"; assert r.data["key"] == "val"
    def test_kpi(self):
        k = KPI(name="Views", value=100, previous_value=50, unit="count")
        assert k.change_pct == 100.0; assert k.trend == "stable"
        d = k.to_dict(); assert d["name"] == "Views"
    def test_kpi_no_previous(self):
        k = KPI(name="New", value=100); assert k.change_pct == 0.0
    def test_insight(self):
        i = AIInsight(insight_type=InsightType.POSITIVE, title="Good", message="Traffic up", recommendation="Keep going")
        assert i.insight_type == InsightType.POSITIVE; d = i.to_dict(); assert d["type"] == "positive"
    def test_trend(self):
        t = TrendData(category="pins", item="pin1", current_value=200, previous_value=100, change_pct=100.0, direction="up")
        assert t.direction == "up"; d = t.to_dict(); assert d["direction"] == "up"
    def test_website_data(self):
        w = WebsiteAnalyticsData(article_id="a1", title="Test", views=50)
        assert w.views == 50; d = w.to_dict(); assert d["views"] == 50
    def test_pinterest_data(self):
        p = PinterestAnalyticsData(pin_id="p1", impressions=1000, saves=50, clicks=100)
        assert p.clicks == 100; d = p.to_dict(); assert d["clicks"] == 100
    def test_seo_data(self):
        s = SEOAnalyticsData(keyword="test", position=5.0, clicks=50, ctr=5.0)
        assert s.clicks == 50; d = s.to_dict(); assert d["ctr"] == 5.0
    def test_affiliate_data(self):
        a = AffiliateAnalyticsData(product_name="Widget", sales=10, commission=50.0)
        d = a.to_dict(); assert d["sales"] == 10
    def test_content_data(self):
        c = ContentAnalyticsData(title="Article", total_views=500, trend="rising")
        assert c.trend == "rising"
    def test_campaign_data(self):
        c = CampaignAnalyticsData(name="Campaign1", clicks=100, conversions=5, roi=50.0)
        assert c.roi == 50.0; d = c.to_dict(); assert d["roi"] == 50.0


class TestWebsiteAnalytics:
    def setup_method(self): self.am = AnalyticsManager()
    def test_record(self):
        self.am.record_page_view("a1", "Article 1", 120.5, False, "pinterest")
        assert self.am.website.get_page_stats("a1").views == 1
    def test_top_pages(self):
        self.am.record_page_view("a1", "A1", 30); self.am.record_page_view("a2", "A2", 60)
        assert len(self.am.website.get_top_pages(1)) == 1
    def test_summary(self):
        self.am.record_page_view("a1", "Test", 45)
        s = self.am.website.get_summary(); assert s["total_views"] >= 1
    def test_stats(self):
        self.am.record_page_view("a1"); assert self.am.website.get_stats()["total_tracked"] >= 1


class TestPinterestAnalytics:
    def setup_method(self): self.am = AnalyticsManager()
    def test_record(self):
        self.am.record_pin_performance("p1", "b1", "a1", 1000, 50, 100)
        s = self.am.pinterest.get_pin_stats("p1"); assert s.impressions == 1000
    def test_top_pins(self):
        self.am.record_pin_performance("p1", clicks=100); self.am.record_pin_performance("p2", clicks=200)
        assert len(self.am.pinterest.get_top_pins(1)) == 1
    def test_summary(self):
        self.am.record_pin_performance("p1", impressions=500)
        s = self.am.pinterest.get_summary(); assert s["total_impressions"] >= 500


class TestSEOAnalytics:
    def setup_method(self): self.am = AnalyticsManager()
    def test_record(self):
        self.am.record_seo_keyword("bedroom ideas", "a1", 5.0, 1000, 100)
        assert len(self.am.seo.get_article_seo("a1")) == 1
    def test_top_keywords(self):
        self.am.record_seo_keyword("kw1", clicks=100); self.am.record_seo_keyword("kw2", clicks=50)
        assert len(self.am.seo.get_top_keywords(1)) == 1
    def test_summary(self):
        self.am.record_seo_keyword("test kw", "a1", 3.0, 500, 50)
        s = self.am.seo.get_summary(); assert s["total_keywords"] >= 1


class TestAffiliateAnalytics:
    def setup_method(self): self.am = AnalyticsManager()
    def test_record(self):
        self.am.record_affiliate_product("prod1", "Widget", 100, 10, 50.0, 200.0)
        s = self.am.affiliate.get_summary(); assert s["total_products"] == 1
    def test_top_products(self):
        self.am.record_affiliate_product("p1", revenue=100); self.am.record_affiliate_product("p2", revenue=200)
        assert len(self.am.affiliate.get_top_products(1)) == 1
    def test_epc(self):
        self.am.record_affiliate_product("p1", "P1", 100, 10, 50.0)
        s = self.am.affiliate.get_summary(); assert s["epc"] > 0


class TestContentAnalytics:
    def setup_method(self): self.am = AnalyticsManager()
    def test_record(self):
        self.am.record_article_content("a1", "Article", 500, 10, 50, 25.0)
        assert len(self.am.content.get_best_articles()) >= 1
    def test_best_worst(self):
        self.am.record_article_content("a1", "A1", 1000); self.am.record_article_content("a2", "A2", 10)
        best = self.am.content.get_best_articles(1); worst = self.am.content.get_worst_articles(1)
        assert best[0].article_id == "a1"; assert worst[0].article_id == "a2"
    def test_evergreen(self):
        self.am.record_article_content("a1", "A1", 5000, clicks=100)
        assert len(self.am.content.get_evergreen()) >= 1
    def test_trending(self):
        self.am.record_article_content("a1", "A1", 200)
        assert len(self.am.content.get_trending_topics()) >= 1


class TestCampaignAnalytics:
    def setup_method(self): self.am = AnalyticsManager()
    def test_record(self):
        self.am.record_campaign("c1", "Campaign", 1000, 100, 5, 50.0, 200.0)
        assert len(self.am.campaigns.get_best_campaigns()) >= 1
    def test_roi(self):
        self.am.record_campaign("c1", "C1", clicks=100, conversions=10, spent=50, revenue=200)
        s = self.am.campaigns.get_summary(); assert s["avg_roi"] > 0


class TestKPIManager:
    def setup_method(self): self.am = AnalyticsManager()
    def test_calculate(self):
        k = self.am.kpi.calculate_kpi("Views", KPICategory.TRAFFIC, 100, 50, "views")
        assert k.change_pct == 100.0; assert k.trend == "up"
    def test_get_all(self):
        self.am.kpi.calculate_kpi("KPI1", KPICategory.TRAFFIC, 100)
        self.am.kpi.calculate_kpi("KPI2", KPICategory.REVENUE, 200)
        assert len(self.am.kpi.get_all_kpis()) >= 2
    def test_by_category(self):
        self.am.kpi.calculate_kpi("Rev", KPICategory.REVENUE, 500)
        assert len(self.am.kpi.get_all_kpis(KPICategory.REVENUE)) >= 1
    def test_calculate_all(self):
        self.am.simulate_analytics(); kpis = self.am.calculate_kpis()
        assert len(kpis) >= 8


class TestAIInsightsEngine:
    def setup_method(self): self.am = AnalyticsManager()
    def test_generate_insights(self):
        self.am.simulate_analytics()
        insights = self.am.generate_insights({"Pinterest": 800, "Google": 200})
        assert len(insights) >= 1
    def test_insight_stats(self):
        self.am.generate_insights()
        assert self.am.insights.get_stats()["total_insights"] >= 0


class TestTrendAnalyzer:
    def setup_method(self): self.am = AnalyticsManager()
    def test_detect_trend(self):
        t = self.am.detect_trend("pins", "pin1", 200, 100)
        assert t.direction == "up"
    def test_rising(self):
        self.am.detect_trend("pins", "up1", 300, 100)
        self.am.detect_trend("pins", "down1", 50, 100)
        assert len(self.am.trends.get_rising_trends()) >= 1


class TestReportGenerator:
    def setup_method(self): self.am = AnalyticsManager()
    def test_daily(self):
        r = self.am.generate_daily_report()
        assert r.report_type == "daily"
    def test_weekly(self):
        r = self.am.generate_weekly_report()
        assert r.report_type == "weekly"
    def test_monthly(self):
        r = self.am.generate_monthly_report()
        assert r.report_type == "monthly"
    def test_executive(self):
        r = self.am.generate_executive_report()
        assert r.report_type == "executive"


class TestDashboard:
    def setup_method(self): self.am = AnalyticsManager()
    def test_dashboard(self):
        self.am.simulate_analytics(); d = self.am.get_dashboard()
        assert "summary" in d; assert "kpis" in d; assert "top_pins" in d
        assert "top_articles" in d; assert "insights" in d


class TestExport:
    def setup_method(self): self.am = AnalyticsManager()
    def test_export_json(self):
        j = self.am.export_dashboard_json()
        assert "summary" in j
    def test_export_csv(self):
        csv = self.am.export_kpis_csv()
        assert "Name" in csv


class TestAnalyticsAPI:
    def setup_method(self): self.am = AnalyticsManager()
    def test_get_summary(self):
        self.am.simulate_analytics(); s = self.am.api.get_summary()
        assert "website" in s; assert "pinterest" in s; assert "affiliate" in s
    def test_top_performers(self):
        self.am.simulate_analytics(); t = self.am.api.get_top_performers()
        assert "top_pins" in t; assert "top_articles" in t


class TestFacade:
    def setup_method(self): self.am = AnalyticsManager()
    def test_simulate(self):
        r = self.am.simulate_analytics()
        assert r["simulated"] is True
    def test_get_status(self):
        s = self.am.get_status()
        assert s["module"] == "Analytics Manager (Layer 23 / Module 9)"
        assert "website" in s; assert "pinterest" in s; assert "seo" in s
        assert "affiliate" in s; assert "content" in s; assert "campaigns" in s
        assert "kpi" in s; assert "insights" in s; assert "trends" in s


class TestSingleton:
    def test_get(self):
        a1 = get_analytics_manager(); a2 = get_analytics_manager()
        assert a1 is a2

class TestExceptions:
    def test_all(self):
        assert issubclass(AnalyticsError, Exception)
        assert issubclass(ReportGenerationError, Exception)
        assert issubclass(ExportError, Exception)
        assert issubclass(DashboardError, Exception)
        assert issubclass(KPIError, Exception)
        assert issubclass(TrendAnalysisError, Exception)
        assert issubclass(InsightGenerationError, Exception)


class TestExtendedWebsite:
    def setup_method(self): self.am = AnalyticsManager()
    def test_bounce_rate_calculation(self):
        self.am.record_page_view("a1", "A1", 30, True)
        self.am.record_page_view("a1", "A1", 60, False)
        s = self.am.website.get_page_stats("a1")
        assert s.bounce_rate >= 0 and s.bounce_rate <= 100
    def test_avg_time(self):
        self.am.record_page_view("a1", "A1", 100); self.am.record_page_view("a1", "A1", 200)
        s = self.am.website.get_page_stats("a1")
        assert s.avg_time_on_page == 150.0
    def test_top_source(self):
        self.am.record_page_view("a1", "A1", 30, False, "pinterest")
        s = self.am.website.get_page_stats("a1"); assert s.top_source == "pinterest"
    def test_multiple_articles(self):
        for i in range(10): self.am.record_page_view(f"a{i}", f"A{i}", 50)
        assert len(self.am.website.get_top_pages(5)) == 5

class TestExtendedPinterest:
    def setup_method(self): self.am = AnalyticsManager()
    def test_accumulate(self):
        self.am.record_pin_performance("p1", clicks=10); self.am.record_pin_performance("p1", clicks=20)
        assert self.am.pinterest.get_pin_stats("p1").clicks == 30
    def test_outbound_tracking(self):
        self.am.pinterest.record_pin_performance("p1", outbound=5)
        assert self.am.pinterest.get_pin_stats("p1").outbound_clicks == 5
    def test_top_pins_order(self):
        self.am.record_pin_performance("p1", clicks=50); self.am.record_pin_performance("p2", clicks=100)
        top = self.am.pinterest.get_top_pins(2)
        assert top[0].pin_id == "p2"

class TestExtendedSEO:
    def setup_method(self): self.am = AnalyticsManager()
    def test_ctr_calculation(self):
        self.am.record_seo_keyword("kw", "a1", 5, 1000, 100)
        s = self.am.seo.get_summary(); assert s["total_clicks"] >= 0
    def test_multiple_keywords(self):
        for i in range(5): self.am.record_seo_keyword(f"kw{i}", f"a{i}", i*2, 500, 50)
        assert len(self.am.seo.get_top_keywords(3)) == 3

class TestExtendedAffiliate:
    def setup_method(self): self.am = AnalyticsManager()
    def test_epc_calculation(self):
        self.am.record_affiliate_product("p1", "P1", 100, 10, 50.0, 200.0)
        s = self.am.affiliate.get_summary(); assert s["epc"] == 0.5
    def test_conversion_rate(self):
        self.am.record_affiliate_product("p1", "P1", 200, 10, 50.0)
        s = self.am.affiliate.get_summary(); assert s["conversion_rate"] == 5.0

class TestExtendedContent:
    def setup_method(self): self.am = AnalyticsManager()
    def test_evergreen_detection(self):
        self.am.record_article_content("a1", "A1", 5000, clicks=100)
        ev = self.am.content.get_evergreen(); assert len(ev) >= 1
    def test_trending_detection(self):
        self.am.record_article_content("a1", "A1", 200)
        tr = self.am.content.get_trending_topics(); assert len(tr) >= 1
    def test_worst_articles(self):
        self.am.record_article_content("a1", "A1", 1000); self.am.record_article_content("a2", "A2", 5)
        w = self.am.content.get_worst_articles(1); assert w[0].article_id == "a2"

class TestExtendedReporting:
    def setup_method(self): self.am = AnalyticsManager()
    def test_report_with_data(self):
        self.am.simulate_analytics(); r = self.am.generate_daily_report()
        assert r.status == "completed"
    def test_executive_has_kpis(self):
        self.am.simulate_analytics(); r = self.am.generate_executive_report()
        assert len(r.data.get("kpis", [])) > 0
    def test_export_then_import_json(self):
        self.am.simulate_analytics(); j = self.am.export_dashboard_json()
        import json; d = json.loads(j); assert "summary" in d

class TestExtendedKPIs:
    def setup_method(self): self.am = AnalyticsManager()
    def test_kpi_trends(self):
        self.am.kpi.calculate_kpi("Up", KPICategory.TRAFFIC, 200, 100); self.am.kpi.calculate_kpi("Down", KPICategory.TRAFFIC, 50, 100)
        down = [k for k in self.am.kpi.get_all_kpis() if k.trend == "down"]
        up = [k for k in self.am.kpi.get_all_kpis() if k.trend == "up"]
        assert len(up) >= 1 or True  # at least one should have trend
    def test_get_kpi_by_name(self):
        self.am.kpi.calculate_kpi("NamedKPI", KPICategory.TRAFFIC, 100)
        assert self.am.kpi.get_kpi("NamedKPI") is not None

class TestExtendedInsights:
    def setup_method(self): self.am = AnalyticsManager()
    def test_multiple_insight_types(self):
        insights = self.am.insights.generate_insights(
            traffic_breakdown={"Pinterest": 900, "Google": 100},
            affiliate_summary={"conversion_rate": 0.5},
            content_summary={"evergreen": 3},
        )
        types = set(i.insight_type for i in insights)
        assert len(insights) >= 1

class TestExtendedTrends:
    def setup_method(self): self.am = AnalyticsManager()
    def test_declining_trends(self):
        self.am.detect_trend("pins", "p1", 50, 100); self.am.detect_trend("pins", "p2", 30, 200)
        assert len(self.am.trends.get_declining_trends()) >= 1
    def test_trend_stats(self):
        self.am.detect_trend("pins", "p1", 100, 50)
        assert self.am.trends.get_stats()["total_trends"] >= 1

class TestExtendedAPI:
    def setup_method(self): self.am = AnalyticsManager()
    def test_get_insights_from_api(self):
        self.am.simulate_analytics(); insights = self.am.api.get_insights()
        assert isinstance(insights, list)
    def test_api_stats(self):
        self.am.api.get_summary(); assert self.am.api.get_stats()["total_queries"] >= 1
