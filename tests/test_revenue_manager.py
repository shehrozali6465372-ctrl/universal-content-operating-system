"""Comprehensive tests for Layer 23 — Module 10: Revenue Manager."""
from __future__ import annotations
import pytest
from layers.layer23_website_manager.revenue_manager.revenue_manager import RevenueManager, get_revenue_manager
from layers.layer23_website_manager.revenue_manager.models.revenue_models import (
    RevenueSource, CommissionRecord, RevenueTransaction, RevenueSummary, Budget,
    RevenueForecast, RevenueAlert, FinancialReport, RevenuePeriod, TransactionStatus, AlertSeverity,
)
from layers.layer23_website_manager.revenue_manager.exceptions import (
    RevenueError, CommissionError, ForecastError, ROIError, BudgetError,
    MerchantRevenueError, FinancialReportError, RevenueAttributionError,
)


class TestModels:
    def test_source(self):
        s = RevenueSource(name="Amazon", network="Amazon", commission_rate=6.0)
        assert s.name == "Amazon"; d = s.to_dict(); assert d["name"] == "Amazon"
    def test_commission(self):
        c = CommissionRecord(amount=50.0, sale_amount=500.0, rate=10.0)
        assert c.status == TransactionStatus.PENDING; d = c.to_dict(); assert d["amount"] == 50.0
    def test_transaction(self):
        t = RevenueTransaction(sale_amount=100.0, commission=10.0, merchant="Amazon")
        assert t.sale_amount == 100.0; d = t.to_dict(); assert d["merchant"] == "Amazon"
    def test_summary(self):
        s = RevenueSummary(gross_revenue=1000, net_profit=500, roi=50.0)
        d = s.to_dict(); assert d["gross_revenue"] == 1000.0
    def test_budget(self):
        b = Budget(name="Ad Spend", allocated=500, spent=200)
        assert b.remaining == 300; assert b.usage_pct == 40.0
    def test_budget_zero_allocated(self):
        b = Budget(name="Free", allocated=0); assert b.usage_pct == 0.0
    def test_forecast(self):
        f = RevenueForecast(predicted_revenue=5000, confidence=0.85)
        d = f.to_dict(); assert d["predicted_revenue"] == 5000.0
    def test_alert(self):
        a = RevenueAlert(severity=AlertSeverity.CRITICAL, title="Drop", message="Revenue down")
        d = a.to_dict(); assert d["severity"] == "critical"
    def test_financial_report(self):
        r = FinancialReport(report_type="monthly", data={"key": "val"})
        assert r.report_type == "monthly"


class TestRevenueSourceManager:
    def setup_method(self): self.rm = RevenueManager()
    def test_register(self):
        s = self.rm.sources.register_source("Test Net", "Test", 10.0)
        assert s.name == "Test Net"; assert self.rm.sources.get_source(s.source_id) is not None
    def test_load_presets(self):
        self.rm.initialize(); assert len(self.rm.sources.get_all_sources()) >= 8
    def test_record_revenue(self):
        s = self.rm.sources.register_source("Rec Test")
        self.rm.sources.record_revenue(s.source_id, 1000, 60)
        assert s.total_revenue == 1000.0; assert s.transaction_count == 1
    def test_top_sources(self):
        s1 = self.rm.sources.register_source("S1"); s2 = self.rm.sources.register_source("S2")
        self.rm.sources.record_revenue(s1.source_id, 500, 30); self.rm.sources.record_revenue(s2.source_id, 1000, 60)
        top = self.rm.sources.get_top_sources(1); assert top[0].name == "S2"
    def test_stats(self):
        self.rm.sources.register_source("Stats"); assert self.rm.sources.get_stats()["total_sources"] >= 1


class TestCommissionTracker:
    def setup_method(self): self.rm = RevenueManager()
    def test_record(self):
        c = self.rm.record_commission("s1", 50.0, 500.0, 10.0)
        assert c.amount == 50.0
    def test_approve(self):
        c = self.rm.record_commission("s1", 50, 500, 10)
        assert self.rm.commissions.approve(c.commission_id) is True
        assert c.status == TransactionStatus.APPROVED
    def test_mark_paid(self):
        c = self.rm.record_commission("s1", 50, 500, 10)
        self.rm.commissions.approve(c.commission_id)
        assert self.rm.commissions.mark_paid(c.commission_id) is True
    def test_reject(self):
        c = self.rm.record_commission("s1", 50, 500, 10)
        assert self.rm.commissions.reject(c.commission_id) is True
        assert c.status == TransactionStatus.REJECTED
    def test_invalid_approve(self):
        assert self.rm.commissions.approve("invalid") is False
    def test_summary(self):
        self.rm.record_commission("s1", 100, 1000, 10)
        s = self.rm.commissions.get_summary(); assert s["total"] >= 1


class TestRevenueAttribution:
    def setup_method(self): self.rm = RevenueManager()
    def test_attribute(self):
        r = self.rm.attribution.attribute(visitor_id="v1", pin_id="p1", article_id="a1", product_id="prod1", sale_amount=100, commission=10)
        assert r["sale_amount"] == 100; assert "attribution_path" in r
    def test_stats(self):
        self.rm.attribution.attribute(visitor_id="v1"); assert self.rm.attribution.get_stats()["total_attributions"] >= 1


class TestProductRevenueAnalyzer:
    def setup_method(self): self.rm = RevenueManager()
    def test_record(self):
        self.rm.products.record_product("p1", "Product 1", "Amazon", 5, 500.0, 30.0, 100)
        s = self.rm.products.get_summary(); assert s["total_products"] == 1
    def test_best_products(self):
        self.rm.products.record_product("p1", revenue=500); self.rm.products.record_product("p2", revenue=1000)
        top = self.rm.products.get_best_products(1); assert top[0]["product_id"] == "p2"
    def test_highest_epc(self):
        self.rm.products.record_product("p1", commission=50, clicks=100)
        self.rm.products.record_product("p2", commission=20, clicks=10)
        top = self.rm.products.get_highest_epc(1); assert top[0]["epc"] == 2.0


class TestMerchantRevenueAnalyzer:
    def setup_method(self): self.rm = RevenueManager()
    def test_record(self):
        self.rm.merchants.record_merchant("Amazon", "general", 10, 1000, 60, 200)
        assert self.rm.merchants.get_summary()["total_merchants"] == 1
    def test_best_merchants(self):
        self.rm.merchants.record_merchant("M1", revenue=500); self.rm.merchants.record_merchant("M2", revenue=1000)
        top = self.rm.merchants.get_best_merchants(1); assert top[0]["merchant_name"] == "M2"


class TestROICalculator:
    def test_calculate(self):
        r = RevenueManager().roi_calc.calculate(1000, 200, 500, 50)
        assert r["roi"] == 400.0; assert r["cost_per_sale"] == 4.0


class TestRevenueForecast:
    def test_daily(self):
        f = RevenueManager().forecast_engine.forecast(100, period=RevenuePeriod.DAILY)
        assert f.predicted_revenue > 0; assert f.confidence > 0
    def test_monthly(self):
        f = RevenueManager().forecast_engine.forecast(100, period=RevenuePeriod.MONTHLY)
        assert f.predicted_revenue >= 3000


class TestRevenueOptimizer:
    def setup_method(self): self.rm = RevenueManager()
    def test_analyze(self):
        r = self.rm.get_optimization()
        assert "suggestions" in r; assert r["count"] > 0


class TestBudgetManager:
    def setup_method(self): self.rm = RevenueManager()
    def test_create(self):
        b = self.rm.budgets.create_budget("marketing", "Ad Spend", 500)
        assert b.allocated == 500; assert b.remaining == 500
    def test_record_spend(self):
        b = self.rm.budgets.create_budget("tools", "API", 200)
        assert self.rm.record_spend(b.budget_id, 50) is True
        assert b.spent == 50; assert b.remaining == 150
    def test_load_presets(self):
        self.rm.initialize(); assert self.rm.budgets.get_summary()["total_budgets"] >= 5
    def test_invalid_spend(self):
        assert self.rm.record_spend("invalid", 50) is False


class TestRevenueAlertManager:
    def setup_method(self): self.rm = RevenueManager()
    def test_create(self):
        a = self.rm.alerts.create_alert(AlertSeverity.WARNING, "Test", "Message")
        assert a.severity == AlertSeverity.WARNING
    def test_unread(self):
        self.rm.alerts.create_alert(AlertSeverity.INFO, "Info", "Test")
        assert len(self.rm.alerts.get_unread()) >= 1
    def test_mark_read(self):
        a = self.rm.alerts.create_alert(AlertSeverity.INFO, "Read", "Test")
        assert self.rm.alerts.mark_read(a.alert_id) is True
    def test_anomaly_spike(self):
        a = self.rm.alerts.check_revenue_anomaly(200, 50)
        assert a is not None; assert "spike" in a.title.lower()
    def test_anomaly_drop(self):
        a = self.rm.alerts.check_revenue_anomaly(10, 100)
        assert a is not None; assert "drop" in a.title.lower()


class TestFinancialReports:
    def setup_method(self): self.rm = RevenueManager()
    def test_daily(self):
        r = self.rm.generate_report("daily"); assert r.report_type == "daily"
    def test_monthly(self):
        r = self.rm.generate_report("monthly"); assert r.report_type == "monthly"
    def test_tax_summary(self):
        r = self.rm.reports.generate_tax_summary(10000, 2000)
        assert r.report_type == "tax"; assert "estimated_tax" in r.data


class TestRevenueAPI:
    def setup_method(self): self.rm = RevenueManager()
    def test_get_summary(self):
        self.rm.initialize(); s = self.rm.api.get_summary()
        assert "sources" in s; assert "commissions" in s; assert "products" in s
    def test_top_revenue(self):
        self.rm.simulate_revenue(3); t = self.rm.api.get_top_revenue()
        assert "top_sources" in t; assert "top_products" in t


class TestFacade:
    def setup_method(self): self.rm = RevenueManager()
    def test_initialize(self):
        r = self.rm.initialize()
        assert r["sources_loaded"] >= 8; assert r["budgets_loaded"] >= 5
    def test_record_transaction(self):
        self.rm.initialize(); s = self.rm.sources.get_all_sources()[0]
        t = self.rm.record_transaction(s.source_id, "Amazon", "prod1", sale_amount=100, commission=6)
        assert t.sale_amount == 100.0
    def test_calculate_roi(self):
        r = self.rm.calculate_roi(1000, 200, 500, 50)
        assert r["roi"] > 0
    def test_forecast(self):
        self.rm.initialize()
        self.rm.simulate_revenue(5)
        f = self.rm.forecast(RevenuePeriod.WEEKLY)
        assert f.predicted_revenue > 0
    def test_get_dashboard(self):
        self.rm.simulate_revenue(5)
        d = self.rm.get_dashboard()
        assert "summary" in d; assert "sources" in d
    def test_simulate(self):
        self.rm.initialize()
        r = self.rm.simulate_revenue(3)
        assert r["simulated"] is True; assert r["transactions"] > 0
    def test_get_status(self):
        self.rm.initialize()
        self.rm.simulate_revenue(3)
        s = self.rm.get_status()
        assert s["module"] == "Revenue Manager (Layer 23 / Module 10)"
        assert s["total_revenue"] > 0


class TestSingleton:
    def test_get(self):
        a1 = get_revenue_manager(); a2 = get_revenue_manager()
        assert a1 is a2


class TestExceptions:
    def test_all(self):
        assert issubclass(RevenueError, Exception)
        assert issubclass(CommissionError, Exception)
        assert issubclass(ForecastError, Exception)
        assert issubclass(ROIError, Exception)
        assert issubclass(BudgetError, Exception)
        assert issubclass(MerchantRevenueError, Exception)
        assert issubclass(FinancialReportError, Exception)
        assert issubclass(RevenueAttributionError, Exception)
