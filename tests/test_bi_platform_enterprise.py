"""Enterprise Business Intelligence Platform Tests — Phase 12."""
import sys
import time
import unittest

sys.path.insert(0, ".")

from layers.layer19_analytics_engine.modules.bi_platform.ceo_dashboard import (
    CEODashboard, DailySnapshot, get_ceo_dashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.revenue_forecasting import (
    RevenueForecasting, ForecastPoint, get_revenue_forecasting,
)
from layers.layer19_analytics_engine.modules.bi_platform.niche_dashboard import (
    NicheDashboard, NicheMetrics, get_niche_dashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.platform_dashboard import (
    PlatformDashboard, PlatformMetrics, get_platform_dashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.ai_dashboard import (
    AIDashboard, AIMetricSnapshot, get_ai_dashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.empire_dashboard import (
    EmpireDashboard, EmpireSnapshot, get_empire_dashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.alert_center import (
    AlertCenter, Alert, get_alert_center,
)
from layers.layer19_analytics_engine.modules.bi_platform.executive_reports import (
    ExecutiveReports, Report, get_executive_reports,
)
from layers.layer19_analytics_engine.modules.bi_platform.api_dashboard import (
    APIDashboard, APIEndpoint, get_api_dashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.bi_manager import (
    BIManager, get_bi_manager,
)


class TestCEODashboard(unittest.TestCase):
    def setUp(self):
        CEODashboard._instance = None
        self.dash = get_ceo_dashboard()

    def tearDown(self):
        CEODashboard._instance = None

    def test_singleton(self):
        self.assertIs(self.dash, get_ceo_dashboard())

    def test_record_daily(self):
        snap = self.dash.record_daily(revenue=500, affiliate_rev=300, expenses=200,
                                        active_accounts=30, posts=15)
        self.assertEqual(snap.total_revenue, 500)
        self.assertEqual(snap.profit, 300)

    def test_monthly_summary(self):
        self.dash.record_daily(date="2026-07-15", revenue=100, expenses=50)
        self.dash.record_daily(date="2026-07-16", revenue=200, expenses=80)
        summary = self.dash.get_monthly_summary()
        self.assertEqual(summary["days"], 2)

    def test_growth_metrics(self):
        self.dash.record_daily(date="2024-01-14", revenue=100)
        self.dash.record_daily(date="2024-01-15", revenue=150)
        growth = self.dash.get_growth_metrics()
        self.assertIn("daily_growth", growth)

    def test_kpi_targets(self):
        self.dash.set_kpi_target("total_revenue", 10000)
        self.dash.record_daily(revenue=500)
        kpis = self.dash.get_kpi_status()
        self.assertIn("total_revenue", kpis)
        self.assertEqual(kpis["total_revenue"]["target"], 10000)

    def test_ceo_summary(self):
        self.dash.record_daily(revenue=100, expenses=30, active_accounts=10)
        summary = self.dash.get_ceo_summary()
        self.assertIn("total_revenue", summary)
        self.assertIn("growth", summary)

    def test_snapshot_dict(self):
        snap = DailySnapshot("2024-01-15")
        snap.total_revenue = 500
        d = snap.to_dict()
        self.assertEqual(d["revenue"], 500)

    def test_profit_margin(self):
        snap = DailySnapshot()
        snap.total_revenue = 1000
        snap.profit = 250
        self.assertEqual(snap.profit_margin, 25.0)


class TestRevenueForecasting(unittest.TestCase):
    def setUp(self):
        RevenueForecasting._instance = None
        self.rf = get_revenue_forecasting()

    def tearDown(self):
        RevenueForecasting._instance = None

    def test_singleton(self):
        self.assertIs(self.rf, get_revenue_forecasting())

    def test_add_historical(self):
        self.rf.add_historical("2024-01-15", revenue=100, profit=50)
        self.assertEqual(len(self.rf._historical), 1)

    def test_forecast_30_days(self):
        self.rf.add_historical("2024-01-14", revenue=100)
        self.rf.add_historical("2024-01-15", revenue=120)
        forecast = self.rf.forecast_30_days()
        self.assertEqual(len(forecast), 30)

    def test_forecast_90_days(self):
        forecast = self.rf.forecast_90_days()
        self.assertEqual(len(forecast), 90)

    def test_forecast_1_year(self):
        forecast = self.rf.forecast_1_year()
        self.assertEqual(len(forecast), 365)

    def test_forecast_summary(self):
        self.rf.add_historical("2024-01-15", revenue=100)
        self.rf.forecast_30_days()
        self.rf.forecast_90_days()
        summary = self.rf.get_forecast_summary()
        self.assertIn("30day", summary)
        self.assertIn("90day", summary)

    def test_roi_forecast(self):
        self.rf.add_historical("2024-01-15", revenue=100)
        self.rf.forecast_30_days()
        roi = self.rf.forecast_roi(investment=500)
        self.assertIn("roi_30day", roi)
        self.assertIn("payback_days", roi)

    def test_full_forecast(self):
        self.rf.add_historical("2024-01-15", revenue=100)
        self.rf.forecast_30_days()
        full = self.rf.get_full_forecast()
        self.assertIn("forecasts", full)
        self.assertIn("roi", full)


class TestNicheDashboard(unittest.TestCase):
    def setUp(self):
        NicheDashboard._instance = None
        self.nd = get_niche_dashboard()

    def tearDown(self):
        NicheDashboard._instance = None

    def test_singleton(self):
        self.assertIs(self.nd, get_niche_dashboard())

    def test_update_niche(self):
        nm = self.nd.update_niche("tech", revenue=500, clicks=1000, accounts=10)
        self.assertEqual(nm.revenue, 500)

    def test_get_top_niches(self):
        self.nd.update_niche("tech", revenue=500, opportunity=80)
        self.nd.update_niche("health", revenue=300, opportunity=60)
        top = self.nd.get_top_niches(2)
        self.assertEqual(len(top), 2)

    def test_get_by_revenue(self):
        self.nd.update_niche("crypto", revenue=1000)
        self.nd.update_niche("tech", revenue=500)
        by_rev = self.nd.get_by_revenue(1)
        self.assertEqual(by_rev[0].name, "crypto")

    def test_get_growing(self):
        self.nd.update_niche("tech", growth_rate=15)
        self.nd.update_niche("health", growth_rate=-5)
        growing = self.nd.get_growing()
        self.assertEqual(len(growing), 1)

    def test_niche_metrics(self):
        nm = NicheMetrics("tech")
        nm.revenue = 1000
        nm.clicks = 5000
        self.assertEqual(nm.conversion_rate, 0)
        self.assertEqual(nm.epc, 0.2)

    def test_dashboard(self):
        self.nd.update_niche("tech", revenue=500)
        dash = self.nd.get_dashboard()
        self.assertIn("total_niches", dash)
        self.assertIn("revenue_share", dash)


class TestPlatformDashboard(unittest.TestCase):
    def setUp(self):
        PlatformDashboard._instance = None
        self.pd = get_platform_dashboard()

    def tearDown(self):
        PlatformDashboard._instance = None

    def test_singleton(self):
        self.assertIs(self.pd, get_platform_dashboard())

    def test_update_platform(self):
        pm = self.pd.update_platform("facebook", reach=10000, engagement=500,
                                       clicks=200, revenue=75)
        self.assertEqual(pm.reach, 10000)
        self.assertEqual(pm.revenue, 75)

    def test_get_top_by_revenue(self):
        self.pd.update_platform("facebook", revenue=100)
        self.pd.update_platform("instagram", revenue=200)
        top = self.pd.get_top_by_revenue(1)
        self.assertEqual(top[0].platform, "instagram")

    def test_platform_metrics(self):
        pm = PlatformMetrics("x")
        pm.reach = 5000
        pm.engagement = 250
        pm.revenue = 50
        self.assertEqual(pm.engagement_rate, 5.0)
        self.assertEqual(pm.rpm, 10.0)

    def test_dashboard(self):
        self.pd.update_platform("facebook", reach=10000, revenue=50)
        dash = self.pd.get_dashboard()
        self.assertIn("total_platforms", dash)
        self.assertIn("revenue_by_platform", dash)


class TestAIDashboard(unittest.TestCase):
    def setUp(self):
        AIDashboard._instance = None
        self.ai = get_ai_dashboard()

    def tearDown(self):
        AIDashboard._instance = None

    def test_singleton(self):
        self.assertIs(self.ai, get_ai_dashboard())

    def test_update_metrics(self):
        snap = self.ai.update_metrics(accuracy=0.85, quality=0.90,
                                        prompt_success=0.80, rag_accuracy=0.75)
        self.assertEqual(snap.accuracy, 0.85)

    def test_current(self):
        self.ai.update_metrics(accuracy=0.80, quality=0.85)
        current = self.ai.get_current()
        self.assertEqual(current.accuracy, 0.80)

    def test_dashboard(self):
        self.ai.update_metrics(accuracy=0.80, quality=0.85)
        dash = self.ai.get_dashboard()
        self.assertIn("current", dash)
        self.assertIn("components", dash)

    def test_component_score(self):
        self.ai.update_component_score("content_gen", 85)
        dash = self.ai.get_dashboard()
        self.assertEqual(dash["components"]["content_gen"], 85)


class TestEmpireDashboard(unittest.TestCase):
    def setUp(self):
        EmpireDashboard._instance = None
        self.ed = get_empire_dashboard()

    def tearDown(self):
        EmpireDashboard._instance = None

    def test_singleton(self):
        self.assertIs(self.ed, get_empire_dashboard())

    def test_update(self):
        snap = self.ed.update(total_accounts=60, active_accounts=55,
                               healthy_accounts=50, published_today=30)
        self.assertEqual(snap.total_accounts, 60)

    def test_health_rate(self):
        snap = EmpireSnapshot()
        snap.active_accounts = 100
        snap.healthy_accounts = 85
        self.assertEqual(snap.health_rate, 85.0)

    def test_dashboard(self):
        self.ed.update(total_accounts=60, active_accounts=55)
        dash = self.ed.get_dashboard()
        self.assertIn("current", dash)


class TestAlertCenter(unittest.TestCase):
    def setUp(self):
        AlertCenter._instance = None
        self.ac = get_alert_center()

    def tearDown(self):
        AlertCenter._instance = None

    def test_singleton(self):
        self.assertIs(self.ac, get_alert_center())

    def test_fire_alert(self):
        alert = self.ac.fire("revenue", "warning", "Revenue drop", "Revenue fell 20%")
        self.assertIsNotNone(alert.id)
        self.assertEqual(alert.severity, "warning")

    def test_acknowledge(self):
        alert = self.ac.fire("account", "critical", "Account banned")
        self.assertTrue(self.ac.acknowledge(alert.id))
        self.assertEqual(alert.status, "acknowledged")

    def test_resolve(self):
        alert = self.ac.fire("api", "info", "API restart")
        self.assertTrue(self.ac.resolve(alert.id))
        self.assertEqual(alert.status, "resolved")

    def test_get_active(self):
        self.ac.fire("revenue", "warning", "Drop")
        self.ac.fire("account", "critical", "Ban")
        active = self.ac.get_active()
        self.assertEqual(len(active), 2)

    def test_get_critical(self):
        self.ac.fire("revenue", "warning", "Drop")
        self.ac.fire("security", "emergency", "Breach")
        critical = self.ac.get_critical()
        self.assertEqual(len(critical), 1)

    def test_alert_summary(self):
        self.ac.fire("revenue", "warning", "Drop")
        self.ac.fire("api", "info", "Restart")
        summary = self.ac.get_alert_summary()
        self.assertIn("total", summary)
        self.assertIn("by_category", summary)


class TestExecutiveReports(unittest.TestCase):
    def setUp(self):
        ExecutiveReports._instance = None
        self.er = get_executive_reports()

    def tearDown(self):
        ExecutiveReports._instance = None

    def test_singleton(self):
        self.assertIs(self.er, get_executive_reports())

    def test_generate_report(self):
        report = self.er.generate_report("daily", "2024-01-15",
                                           sections=[{"title": "Revenue", "data": {}}])
        self.assertIsNotNone(report.id)

    def test_get_by_type(self):
        self.er.generate_report("daily", "2024-01-15")
        self.er.generate_report("weekly", "2024-W03")
        daily = self.er.get_by_type("daily")
        self.assertEqual(len(daily), 1)

    def test_get_latest(self):
        self.er.generate_report("daily", "2024-01-15")
        latest = self.er.get_latest("daily")
        self.assertIsNotNone(latest)

    def test_reports_status(self):
        self.er.generate_report("daily", "2024-01-15")
        status = self.er.get_reports_status()
        self.assertIn("total_reports", status)


class TestAPIDashboard(unittest.TestCase):
    def setUp(self):
        APIDashboard._instance = None
        self.api = get_api_dashboard()

    def tearDown(self):
        APIDashboard._instance = None

    def test_singleton(self):
        self.assertIs(self.api, get_api_dashboard())

    def test_default_endpoints(self):
        endpoints = self.api.get_all_endpoints()
        self.assertGreater(len(endpoints), 0)

    def test_register_endpoint(self):
        ep = self.api.register_endpoint("/api/v1/custom", "POST", "Custom endpoint")
        self.assertIsNotNone(ep)

    def test_log_request(self):
        self.api.log_request("/api/v1/status", latency_ms=15.5, status=200)
        stats = self.api.get_request_stats()
        self.assertEqual(stats["total_requests"], 1)

    def test_api_status(self):
        status = self.api.get_api_status()
        self.assertIn("total_endpoints", status)
        self.assertIn("total_requests", status)


class TestBIManager(unittest.TestCase):
    def setUp(self):
        for cls in [CEODashboard, RevenueForecasting, NicheDashboard,
                     PlatformDashboard, AIDashboard, EmpireDashboard,
                     AlertCenter, ExecutiveReports, APIDashboard, BIManager]:
            cls._instance = None
        self.bi = get_bi_manager()

    def tearDown(self):
        for cls in [CEODashboard, RevenueForecasting, NicheDashboard,
                     PlatformDashboard, AIDashboard, EmpireDashboard,
                     AlertCenter, ExecutiveReports, APIDashboard, BIManager]:
            cls._instance = None

    def test_singleton(self):
        self.assertIs(self.bi, get_bi_manager())

    def test_submodules(self):
        self.assertIsNotNone(self.bi.ceo)
        self.assertIsNotNone(self.bi.forecasting)
        self.assertIsNotNone(self.bi.niche)
        self.assertIsNotNone(self.bi.platform)
        self.assertIsNotNone(self.bi.ai)
        self.assertIsNotNone(self.bi.empire)
        self.assertIsNotNone(self.bi.alerts)
        self.assertIsNotNone(self.bi.reports)
        self.assertIsNotNone(self.bi.api)

    def test_full_bi_status(self):
        status = self.bi.get_full_bi_status()
        self.assertEqual(status["overall"], "Active")
        self.assertIn("ceo", status)
        self.assertIn("forecasting", status)
        self.assertIn("niche", status)
        self.assertIn("platform", status)
        self.assertIn("ai", status)
        self.assertIn("empire", status)
        self.assertIn("alerts", status)

    def test_executive_summary(self):
        summary = self.bi.get_executive_summary()
        self.assertIn("total_revenue", summary)
        self.assertIn("total_accounts", summary)

    def test_generate_daily_report(self):
        self.bi.ceo.record_daily(revenue=100, active_accounts=10)
        result = self.bi.generate_daily_report()
        self.assertIn("report", result)
        self.assertIn("data", result)

    def test_stats(self):
        s = self.bi.stats()
        self.assertIn("ceo", s)
        self.assertIn("forecasting", s)


class TestFullEnterpriseStack(unittest.TestCase):
    def setUp(self):
        for cls in [CEODashboard, RevenueForecasting, NicheDashboard,
                     PlatformDashboard, AIDashboard, EmpireDashboard,
                     AlertCenter, ExecutiveReports, APIDashboard, BIManager]:
            cls._instance = None
        self.bi = get_bi_manager()

    def tearDown(self):
        for cls in [CEODashboard, RevenueForecasting, NicheDashboard,
                     PlatformDashboard, AIDashboard, EmpireDashboard,
                     AlertCenter, ExecutiveReports, APIDashboard, BIManager]:
            cls._instance = None

    def test_full_bi_flow(self):
        # 1. CEO data
        self.bi.ceo.record_daily(date="2024-01-14", revenue=100, expenses=40)
        self.bi.ceo.record_daily(date="2024-01-15", revenue=150, expenses=50)
        self.bi.ceo.set_kpi_target("total_revenue", 10000)
        # 2. Forecasting
        self.bi.forecasting.add_historical("2024-01-14", revenue=100)
        self.bi.forecasting.add_historical("2024-01-15", revenue=150)
        self.bi.forecasting.forecast_30_days()
        self.bi.forecasting.forecast_90_days()
        self.bi.forecasting.forecast_roi(investment=500)
        # 3. Niches
        self.bi.niche.update_niche("tech", revenue=500, clicks=1000, accounts=10,
                                     growth_rate=15, opportunity=80)
        self.bi.niche.update_niche("health", revenue=300, clicks=800, accounts=8)
        # 4. Platforms
        self.bi.platform.update_platform("facebook", reach=50000, engagement=2500,
                                            clicks=500, revenue=100)
        self.bi.platform.update_platform("instagram", reach=30000, engagement=1500,
                                            clicks=300, revenue=75)
        # 5. AI
        self.bi.ai.update_metrics(accuracy=0.85, quality=0.90,
                                    prompt_success=0.80, rag_accuracy=0.75,
                                    predictions=1000, correct=850)
        # 6. Empire
        self.bi.empire.update(total_accounts=60, active_accounts=55,
                                healthy_accounts=50, published_today=30)
        # 7. Alerts
        self.bi.alerts.fire("revenue", "warning", "Revenue drop detected")
        self.bi.alerts.fire("account", "critical", "Shadow ban detected")
        # 8. Reports
        self.bi.reports.generate_report("daily", "2024-01-15",
                                          sections=[{"title": "Revenue"}])
        # 9. API
        self.bi.api.log_request("/api/v1/ceo", latency_ms=25.0)

        # Verify full status
        status = self.bi.get_full_bi_status()
        self.assertEqual(status["overall"], "Active")
        self.assertGreater(status["ceo"]["total_revenue"], 0)

        # Verify executive summary
        summary = self.bi.get_executive_summary()
        self.assertGreater(summary["total_revenue"], 0)
        self.assertEqual(summary["total_accounts"], 60)

        # Verify daily report
        report = self.bi.generate_daily_report()
        self.assertIn("report", report)

        # Verify forecasting
        forecast = self.bi.forecasting.get_full_forecast()
        self.assertIn("forecasts", forecast)
        self.assertIn("roi", forecast)


if __name__ == "__main__":
    unittest.main()
