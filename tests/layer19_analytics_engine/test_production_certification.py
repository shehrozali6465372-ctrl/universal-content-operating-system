"""Layer 19 production certification gates.

These tests target executable production contracts: validation, idempotency,
bounded in-memory state, concurrency safety, finite analytics, and full-stack
integration. No synthetic external-provider success is used.
"""
from __future__ import annotations

import math
import threading
import unittest

from layers.layer19_analytics_engine.modules.bi_platform.ai_dashboard import (
    AIDashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.alert_center import (
    AlertCenter,
)
from layers.layer19_analytics_engine.modules.bi_platform.api_dashboard import (
    APIDashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.bi_manager import (
    BIManager,
)
from layers.layer19_analytics_engine.modules.bi_platform.ceo_dashboard import (
    CEODashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.empire_dashboard import (
    EmpireDashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.executive_reports import (
    ExecutiveReports,
)
from layers.layer19_analytics_engine.modules.bi_platform.niche_dashboard import (
    NicheDashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.platform_dashboard import (
    PlatformDashboard,
)
from layers.layer19_analytics_engine.modules.bi_platform.revenue_forecasting import (
    RevenueForecasting,
)


def reset_singletons() -> None:
    for cls in (
        AIDashboard,
        AlertCenter,
        APIDashboard,
        BIManager,
        CEODashboard,
        EmpireDashboard,
        ExecutiveReports,
        NicheDashboard,
        PlatformDashboard,
        RevenueForecasting,
    ):
        cls._instance = None


class TestLayer19ProductionContracts(unittest.TestCase):
    def setUp(self) -> None:
        reset_singletons()

    def tearDown(self) -> None:
        reset_singletons()

    def test_ceo_first_snapshot_and_replacement_are_atomic(self) -> None:
        dashboard = CEODashboard()
        dashboard.record_daily(
            date="2026-01-01",
            revenue=100,
            expenses=40,
            active_accounts=12,
            clicks=10,
            conversions=2,
        )
        self.assertEqual(dashboard.get_ceo_summary()["total_revenue"], 100)
        self.assertEqual(dashboard.get_ceo_summary()["total_accounts"], 12)
        dashboard.record_daily(
            date="2026-01-01",
            revenue=150,
            expenses=50,
            active_accounts=14,
            clicks=20,
            conversions=4,
        )
        summary = dashboard.get_ceo_summary()
        self.assertEqual(summary["total_revenue"], 150)
        self.assertEqual(summary["total_clicks"], 20)
        self.assertEqual(summary["total_accounts"], 14)

    def test_invalid_financial_and_metric_inputs_fail_closed(self) -> None:
        dashboard = CEODashboard()
        with self.assertRaises(ValueError):
            dashboard.record_daily(revenue=float("nan"))
        with self.assertRaises(ValueError):
            dashboard.record_daily(clicks=-1)

        ai = AIDashboard()
        with self.assertRaises(ValueError):
            ai.update_metrics(accuracy=1.1)
        with self.assertRaises(ValueError):
            ai.update_metrics(predictions=1, correct=2)

        niche = NicheDashboard()
        with self.assertRaises(ValueError):
            niche.update_niche("tech", competition=101)

        platform = PlatformDashboard()
        with self.assertRaises(ValueError):
            platform.update_platform("facebook", reach=-1)

        empire = EmpireDashboard()
        with self.assertRaises(ValueError):
            empire.update(total_accounts=1, active_accounts=2)

    def test_forecast_requires_real_observations_and_emits_finite_values(self) -> None:
        forecasting = RevenueForecasting()
        with self.assertRaises(ValueError):
            forecasting.forecast_30_days()
        forecasting.add_historical("2026-01-01", 100, profit=30)
        forecasting.add_historical("2026-01-02", 120, profit=40)
        points = forecasting.forecast_30_days()
        self.assertEqual(len(points), 30)
        for point in points:
            self.assertTrue(
                all(
                    math.isfinite(value)
                    for value in (
                        point.predicted_revenue,
                        point.predicted_profit,
                        point.confidence,
                        point.lower_bound,
                        point.upper_bound,
                    )
                )
            )
        with self.assertRaises(ValueError):
            forecasting.forecast_roi(float("nan"))
        with self.assertRaises(ValueError):
            forecasting.forecast_roi(0)

    def test_api_endpoint_registration_is_idempotent(self) -> None:
        api = APIDashboard()
        before = api.get_api_status()["total_endpoints"]
        first = api.register_endpoint("/api/v1/idempotent", "GET", "one")
        second = api.register_endpoint("/api/v1/idempotent", "GET", "two")
        self.assertIs(first, second)
        self.assertEqual(api.get_api_status()["total_endpoints"], before + 1)
        with self.assertRaises(ValueError):
            api.register_endpoint("/api/v1/idempotent", "POST", "wrong")

    def test_in_memory_retention_is_bounded(self) -> None:
        ai = AIDashboard()
        for _ in range(1100):
            ai.update_metrics(accuracy=0.8, quality=0.8, prompt_success=0.8, rag_accuracy=0.8)
        self.assertLessEqual(ai.stats()["snapshots"], 1000)

        alerts = AlertCenter()
        for _ in range(11050):
            alerts.fire("system", "info", "retention")
        self.assertLessEqual(len(alerts._alert_history), 5000)

        reports = ExecutiveReports()
        for i in range(10020):
            reports.generate_report("daily", f"2026-{(i % 12) + 1:02d}-01")
        self.assertLessEqual(reports.stats()["reports"], 10000)

        api = APIDashboard()
        for _ in range(10050):
            api.log_request("/api/v1/status", latency_ms=1)
        self.assertLessEqual(len(api._request_log), 10000)

    def test_concurrent_updates_do_not_corrupt_state(self) -> None:
        platform = PlatformDashboard()
        errors: list[BaseException] = []

        def worker() -> None:
            try:
                for _ in range(100):
                    platform.update_platform("facebook", reach=10, clicks=1, revenue=1)
                    platform.get_dashboard()
            except BaseException as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        self.assertEqual(platform.get_platform("facebook").reach, 12000)

    def test_full_layer19_control_plane_flow(self) -> None:
        bi = BIManager()
        bi.ceo.record_daily(date="2026-01-01", revenue=100, expenses=40, active_accounts=10)
        bi.ceo.record_daily(date="2026-01-02", revenue=120, expenses=50, active_accounts=12)
        bi.forecasting.add_historical("2026-01-01", revenue=100, profit=60)
        bi.forecasting.add_historical("2026-01-02", revenue=120, profit=70)
        bi.forecasting.forecast_30_days()
        bi.forecasting.forecast_90_days()
        bi.forecasting.forecast_1_year()
        bi.forecasting.forecast_roi(100)
        bi.niche.update_niche("technology", revenue=100, clicks=50, accounts=2)
        bi.platform.update_platform("facebook", reach=1000, clicks=20, revenue=10)
        bi.ai.update_metrics(accuracy=0.9, quality=0.9, prompt_success=0.95, rag_accuracy=0.85)
        bi.empire.update(total_accounts=12, active_accounts=10, healthy_accounts=9)
        bi.alerts.fire("system", "info", "certification")
        result = bi.generate_daily_report()
        self.assertIn("report", result)
        status = bi.get_full_bi_status()
        self.assertEqual(status["overall"], "Active")
        self.assertTrue(math.isfinite(status["ceo"]["total_revenue"]))
        self.assertIn("forecasting", status)


if __name__ == "__main__":
    unittest.main()
