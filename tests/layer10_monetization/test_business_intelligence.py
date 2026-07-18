"""Tests for Layer 10 Module 9 — Business Intelligence & Revenue Engine."""
from layers.layer10_monetization.modules.business_intelligence.revenue_tracker import (
    RevenueTracker,
)
from layers.layer10_monetization.modules.business_intelligence.roi_analyzer import (
    ROIAnalyzer,
)
from layers.layer10_monetization.modules.business_intelligence.campaign_manager import (
    CampaignManager,
)
from layers.layer10_monetization.modules.business_intelligence.budget_planner import (
    BudgetPlanner,
)
from layers.layer10_monetization.modules.business_intelligence.business_forecaster import (
    BusinessForecaster,
)
from layers.layer10_monetization.modules.business_intelligence.opportunity_detector import (
    OpportunityDetector,
)
from layers.layer10_monetization.modules.business_intelligence.monetization_optimizer import (
    MonetizationOptimizer,
)
from layers.layer10_monetization.modules.business_intelligence.financial_memory import (
    FinancialMemory,
)
from layers.layer10_monetization.modules.business_intelligence.business_metrics import BusinessMetrics
from layers.layer10_monetization.modules.business_intelligence.business_report import (
    BusinessReportGenerator,
)
from layers.layer10_monetization.modules.business_intelligence.business_intelligence_api import (
    BusinessIntelligenceAPI,
)
from layers.layer10_monetization.modules.business_intelligence.business_orchestrator import (
    BusinessOrchestrator,
)
from layers.layer10_monetization.modules.business_intelligence.exceptions import (
    BusinessError, RevenueError, ROIError, CampaignError,
    BudgetError, ForecastError, OpportunityError, FinancialMemoryError,
)


# ─── RevenueTracker Tests ──────────────────────────────────────
class TestRevenueTracker:
    def setup_method(self):
        self.rt = RevenueTracker()

    def test_record(self):
        entry = self.rt.record("ad_revenue", 150.0, "facebook", "ads")
        assert entry.entry_id.startswith("rev_")
        assert entry.amount == 150.0
        assert entry.revenue_type == "ad_revenue"

    def test_record_invalid_type(self):
        entry = self.rt.record("invalid_type", 50.0)
        assert entry.revenue_type == "other"

    def test_record_negative_amount(self):
        entry = self.rt.record("ad_revenue", -10.0)
        assert entry.amount == 0.0

    def test_get_total_revenue(self):
        self.rt.record("ad_revenue", 100.0, "facebook")
        self.rt.record("affiliate", 50.0, "facebook")
        assert self.rt.get_total_revenue("facebook") == 150.0

    def test_get_total_revenue_all(self):
        self.rt.record("ad_revenue", 100.0, "facebook")
        self.rt.record("ad_revenue", 200.0, "linkedin")
        assert self.rt.get_total_revenue() == 300.0

    def test_get_by_type(self):
        self.rt.record("ad_revenue", 100.0)
        self.rt.record("affiliate", 50.0)
        assert len(self.rt.get_by_type("ad_revenue")) == 1

    def test_get_by_platform(self):
        self.rt.record("ad_revenue", 100.0, "facebook")
        self.rt.record("ad_revenue", 200.0, "x")
        assert len(self.rt.get_by_platform("facebook")) == 1

    def test_get_revenue_breakdown(self):
        self.rt.record("ad_revenue", 100.0)
        self.rt.record("affiliate", 50.0)
        self.rt.record("ad_revenue", 200.0)
        breakdown = self.rt.get_revenue_breakdown()
        assert breakdown["ad_revenue"] == 300.0
        assert breakdown["affiliate"] == 50.0

    def test_get_daily_revenue(self):
        self.rt.record("ad_revenue", 100.0)
        daily = self.rt.get_daily_revenue()
        assert daily == 100.0

    def test_get_entry_count(self):
        self.rt.record("ad_revenue", 100.0)
        self.rt.record("affiliate", 50.0)
        assert self.rt.get_entry_count() == 2

    def test_get_stats(self):
        self.rt.record("ad_revenue", 100.0, "facebook")
        stats = self.rt.get_stats()
        assert stats["total_entries"] == 1
        assert stats["total_revenue"] == 100.0


# ─── ROIAnalyzer Tests ─────────────────────────────────────────
class TestROIAnalyzer:
    def setup_method(self):
        self.analyzer = ROIAnalyzer()

    def test_calculate_basic(self):
        snap = self.analyzer.calculate("facebook", revenue=500, cost=200)
        assert snap.snapshot_id.startswith("roi_")
        assert snap.roi == 1.5  # (500-200)/200
        assert snap.roas == 2.5  # 500/200
        assert snap.profit_margin == 0.6  # (500-200)/500

    def test_calculate_with_impressions(self):
        snap = self.analyzer.calculate("x", revenue=300, cost=100,
                                        impressions=10000, clicks=200)
        assert snap.cpm == 10.0  # (100/10000)*1000
        assert snap.cpc == 0.5   # 100/200

    def test_calculate_with_conversions(self):
        snap = self.analyzer.calculate("linkedin", revenue=1000, cost=300,
                                        conversions=10, leads=50)
        assert snap.cpa == 30.0   # 300/10
        assert snap.cpl == 6.0    # 300/50

    def test_calculate_ltv(self):
        snap = self.analyzer.calculate("facebook", revenue=200, cost=100,
                                        customer_lifespan_months=24,
                                        monthly_revenue_per_customer=10.0)
        assert snap.ltv == 240.0

    def test_calculate_zero_cost(self):
        snap = self.analyzer.calculate("x", revenue=100, cost=0)
        assert snap.roi == 0.0
        assert snap.roas == 0.0

    def test_calculate_batch(self):
        items = [{"platform": "facebook", "revenue": 500, "cost": 200},
                 {"platform": "x", "revenue": 300, "cost": 100}]
        results = self.analyzer.calculate_batch(items)
        assert len(results) == 2

    def test_compare_platforms(self):
        self.analyzer.calculate("facebook", revenue=500, cost=200)
        self.analyzer.calculate("facebook", revenue=400, cost=150)
        self.analyzer.calculate("x", revenue=200, cost=100)
        comparison = self.analyzer.compare_platforms()
        assert len(comparison) == 2
        assert comparison[0]["avg_roi"] >= comparison[1]["avg_roi"]

    def test_get_trend(self):
        self.analyzer.calculate("facebook", revenue=100, cost=50)
        self.analyzer.calculate("facebook", revenue=200, cost=80)
        trend = self.analyzer.get_trend("facebook")
        assert len(trend) == 2
        assert "roi" in trend[0]

    def test_get_latest(self):
        self.analyzer.calculate("x", revenue=100, cost=50)
        self.analyzer.calculate("facebook", revenue=300, cost=100)
        latest = self.analyzer.get_latest("facebook")
        assert latest is not None
        assert latest.platform == "facebook"

    def test_get_latest_none(self):
        assert self.analyzer.get_latest("unknown") is None

    def test_stats(self):
        self.analyzer.calculate("fb", revenue=100, cost=50)
        stats = self.analyzer.get_stats()
        assert stats["total_snapshots"] == 1


# ─── CampaignManager Tests ─────────────────────────────────────
class TestCampaignManager:
    def setup_method(self):
        self.cm = CampaignManager()

    def test_create(self):
        camp = self.cm.create("Summer Sale", "marketing", ["facebook", "x"], 5000)
        assert camp.campaign_id.startswith("camp_")
        assert camp.name == "Summer Sale"
        assert camp.budget == 5000
        assert "facebook" in camp.platforms

    def test_create_invalid_type(self):
        camp = self.cm.create("Test", "invalid_type")
        assert camp.campaign_type == "marketing"

    def test_get(self):
        camp = self.cm.create("Test")
        retrieved = self.cm.get(camp.campaign_id)
        assert retrieved is not None
        assert retrieved.name == "Test"

    def test_get_not_found(self):
        assert self.cm.get("camp_99999") is None

    def test_update_status(self):
        camp = self.cm.create("Test")
        assert self.cm.update_status(camp.campaign_id, "active") is True
        assert camp.status == "active"

    def test_update_status_invalid(self):
        camp = self.cm.create("Test")
        assert self.cm.update_status(camp.campaign_id, "invalid") is False

    def test_record_spend(self):
        camp = self.cm.create("Test", budget=1000)
        self.cm.record_spend(camp.campaign_id, 250)
        assert camp.spent == 250
        assert camp.get_remaining_budget() == 750

    def test_record_revenue(self):
        camp = self.cm.create("Test", budget=1000)
        self.cm.record_spend(camp.campaign_id, 500)
        self.cm.record_revenue(camp.campaign_id, 2000)
        assert camp.revenue == 2000
        assert camp.get_roi() == 3.0  # (2000-500)/500

    def test_get_active(self):
        c1 = self.cm.create("Active 1")
        c2 = self.cm.create("Active 2")
        self.cm.update_status(c1.campaign_id, "active")
        active = self.cm.get_active()
        assert len(active) == 1

    def test_get_by_type(self):
        self.cm.create("Marketing 1", "marketing")
        self.cm.create("Sponsorship 1", "sponsorship")
        marketing = self.cm.get_by_type("marketing")
        assert len(marketing) == 1

    def test_get_by_platform(self):
        self.cm.create("A", platforms=["facebook", "x"])
        self.cm.create("B", platforms=["linkedin"])
        fb = self.cm.get_by_platform("facebook")
        assert len(fb) == 1

    def test_get_top_performing(self):
        c1 = self.cm.create("Low ROI")
        c2 = self.cm.create("High ROI")
        self.cm.record_spend(c1.campaign_id, 500)
        self.cm.record_revenue(c1.campaign_id, 600)
        self.cm.record_spend(c2.campaign_id, 500)
        self.cm.record_revenue(c2.campaign_id, 5000)
        top = self.cm.get_top_performing(1)
        assert top[0].name == "High ROI"

    def test_totals(self):
        c1 = self.cm.create("A", budget=1000)
        c2 = self.cm.create("B", budget=2000)
        self.cm.record_spend(c1.campaign_id, 300)
        self.cm.record_spend(c2.campaign_id, 600)
        assert self.cm.get_total_budget() == 3000
        assert self.cm.get_total_spent() == 900

    def test_stats(self):
        self.cm.create("A", "marketing")
        self.cm.create("B", "sponsorship")
        stats = self.cm.get_stats()
        assert stats["total"] == 2
        assert stats["by_type"]["marketing"] == 1


# ─── BudgetPlanner Tests ───────────────────────────────────────
class TestBudgetPlanner:
    def setup_method(self):
        self.bp = BudgetPlanner(total_budget=10000)

    def test_allocate(self):
        alloc = self.bp.allocate("ai_api", 500)
        assert alloc.allocation_id.startswith("balloc_")
        assert alloc.allocated == 500
        assert alloc.get_remaining() == 500

    def test_allocate_accumulate(self):
        self.bp.allocate("ai_api", 500)
        self.bp.allocate("ai_api", 300)
        alloc = self.bp.get_allocation("ai_api")
        assert alloc.allocated == 800

    def test_record_spend(self):
        self.bp.allocate("ai_api", 500)
        self.bp.record_spend("ai_api", 200)
        alloc = self.bp.get_allocation("ai_api")
        assert alloc.spent == 200
        assert alloc.get_remaining() == 300

    def test_record_spend_unknown_category(self):
        assert self.bp.record_spend("unknown", 100) is False

    def test_reserve(self):
        self.bp.allocate("gpu", 1000)
        assert self.bp.reserve("gpu", 300) is True
        alloc = self.bp.get_allocation("gpu")
        assert alloc.reserved == 300
        assert alloc.get_remaining() == 700

    def test_reserve_exceeds(self):
        self.bp.allocate("gpu", 100)
        assert self.bp.reserve("gpu", 200) is False

    def test_utilization(self):
        self.bp.allocate("marketing", 1000)
        self.bp.record_spend("marketing", 600)
        alloc = self.bp.get_allocation("marketing")
        assert alloc.get_utilization() == 0.6

    def test_forecast(self):
        for _ in range(5):
            self.bp.allocate("ai_api", 100)
            self.bp.record_spend("ai_api", 10)
        days = self.bp.forecast_remaining_days()
        assert days > 0

    def test_total_spent(self):
        self.bp.allocate("a", 100)
        self.bp.allocate("b", 100)
        self.bp.record_spend("a", 30)
        self.bp.record_spend("b", 20)
        assert self.bp.get_total_spent() == 50

    def test_total_remaining(self):
        self.bp.allocate("a", 100)
        self.bp.record_spend("a", 30)
        assert self.bp.get_total_remaining() == 70

    def test_utilization_report(self):
        self.bp.allocate("ai_api", 100)
        self.bp.record_spend("ai_api", 50)
        report = self.bp.get_utilization_report()
        assert report["ai_api"] == 0.5

    def test_set_total_budget(self):
        self.bp.set_total_budget(50000)
        assert self.bp._total_budget == 50000

    def test_stats(self):
        self.bp.allocate("ai_api", 500)
        stats = self.bp.get_stats()
        assert stats["allocations"] == 1
        assert stats["total_budget"] == 10000

    def test_invalid_category(self):
        alloc = self.bp.allocate("unknown_cat", 100)
        assert alloc.category == "other"


# ─── BusinessForecaster Tests ──────────────────────────────────
class TestBusinessForecaster:
    def setup_method(self):
        self.bf = BusinessForecaster()

    def test_forecast(self):
        result = self.bf.forecast("revenue", "revenue", "next_month",
                                   [1000, 1100, 1200])
        assert result.forecast_id.startswith("fcst_")
        assert result.predicted_value > 0
        assert result.confidence > 0

    def test_forecast_single_value(self):
        result = self.bf.forecast("revenue", "revenue", "next_week", [1000])
        assert result.predicted_value == 1000
        assert result.confidence == 0.2

    def test_forecast_empty(self):
        result = self.bf.forecast("revenue", "revenue", "next_quarter")
        assert result.predicted_value == 0.0

    def test_forecast_with_factors(self):
        result = self.bf.forecast("revenue", "revenue", "next_month",
                                   [1000, 1200], factors=["seasonal_boost"])
        assert "seasonal_boost" in result.factors

    def test_forecast_revenue(self):
        result = self.bf.forecast_revenue("next_month", 5000, 0.15)
        assert result.predicted_value == 5750.0
        assert result.forecast_type == "revenue"

    def test_forecast_growth(self):
        result = self.bf.forecast_growth("next_quarter", "users",
                                          [100, 120, 150])
        assert result.predicted_value > 0

    def test_get_forecasts(self):
        self.bf.forecast_revenue("next_month", 5000, 0.1)
        self.bf.forecast("expense", "cost", "next_month", [2000, 2100])
        assert len(self.bf.get_forecasts("revenue")) == 1
        assert len(self.bf.get_forecasts()) == 2

    def test_get_latest_forecast(self):
        self.bf.forecast_revenue("next_month", 5000, 0.1)
        self.bf.forecast_revenue("next_month", 6000, 0.2)
        latest = self.bf.get_latest_forecast("revenue")
        assert latest.predicted_value == 7200  # 6000 * 1.2

    def test_get_latest_none(self):
        assert self.bf.get_latest_forecast("revenue") is None

    def test_stats(self):
        self.bf.forecast_revenue("next_month", 5000, 0.1)
        stats = self.bf.get_stats()
        assert stats["total_forecasts"] == 1


# ─── OpportunityDetector Tests ─────────────────────────────────
class TestOpportunityDetector:
    def setup_method(self):
        self.od = OpportunityDetector()

    def test_detect(self):
        opp = self.od.detect("affiliate", "Amazon Program", "facebook", 500.0)
        assert opp.opportunity_id.startswith("opp_")
        assert opp.title == "Amazon Program"
        assert opp.estimated_revenue == 500.0

    def test_detect_invalid_type(self):
        opp = self.od.detect("invalid", "Test")
        assert opp.opportunity_type == "other"

    def test_get_top_opportunities(self):
        self.od.detect("affiliate", "A", "facebook", 100.0)
        self.od.detect("sponsorship", "B", "facebook", 500.0)
        top = self.od.get_top_opportunities(1)
        assert top[0].title == "B"

    def test_get_by_type(self):
        self.od.detect("affiliate", "A")
        self.od.detect("sponsorship", "B")
        affiliates = self.od.get_by_type("affiliate")
        assert len(affiliates) == 1

    def test_get_by_platform(self):
        self.od.detect("affiliate", "A", "facebook")
        self.od.detect("affiliate", "B", "x")
        fb = self.od.get_by_platform("facebook")
        assert len(fb) == 1

    def test_mark_accepted(self):
        opp = self.od.detect("sponsorship", "Big Deal")
        assert self.od.mark_accepted(opp.opportunity_id) is True
        assert opp.status == "accepted"

    def test_mark_rejected(self):
        opp = self.od.detect("affiliate", "Small Deal")
        assert self.od.mark_rejected(opp.opportunity_id) is True
        assert opp.status == "rejected"

    def test_mark_not_found(self):
        assert self.od.mark_accepted("opp_99999") is False

    def test_get_pending(self):
        opp = self.od.detect("affiliate", "Pending")
        pending = self.od.get_pending()
        assert len(pending) == 1

    def test_get_total_estimated_revenue(self):
        self.od.detect("affiliate", "A", "facebook", 100.0)
        self.od.detect("affiliate", "B", "facebook", 200.0)
        assert self.od.get_total_estimated_revenue("facebook") == 300.0

    def test_stats(self):
        self.od.detect("affiliate", "A", "facebook")
        self.od.detect("sponsorship", "B", "x")
        stats = self.od.get_stats()
        assert stats["total"] == 2


# ─── MonetizationOptimizer Tests ───────────────────────────────
class TestMonetizationOptimizer:
    def setup_method(self):
        self.mo = MonetizationOptimizer()

    def test_suggest(self):
        strategy = self.mo.suggest("ad_placement", "facebook", 1000.0,
                                    "Optimize ad positions")
        assert strategy.strategy_id.startswith("ms_")
        assert strategy.expected_revenue == 1000.0

    def test_get_top_strategies(self):
        self.mo.suggest("ad_placement", "facebook", 500.0)
        self.mo.suggest("affiliate", "facebook", 1000.0)
        top = self.mo.get_top_strategies(1, "facebook")
        assert top[0].strategy_id != ""

    def test_record_outcome(self):
        strategy = self.mo.suggest("ad_placement", "facebook", 1000.0)
        assert self.mo.record_outcome(strategy.strategy_id, 800.0) is True

    def test_record_outcome_not_found(self):
        assert self.mo.record_outcome("ms_99999", 100.0) is False

    def test_get_accuracy(self):
        strategy = self.mo.suggest("ad_placement", "facebook", 1000.0)
        self.mo.record_outcome(strategy.strategy_id, 800.0)
        accuracy = self.mo.get_accuracy()
        assert "ad_placement:facebook" in accuracy
        assert accuracy["ad_placement:facebook"] == 0.8

    def test_get_by_platform(self):
        self.mo.suggest("ad", "facebook")
        self.mo.suggest("ad", "x")
        assert len(self.mo.get_by_platform("facebook")) == 1

    def test_get_by_type(self):
        self.mo.suggest("ad_placement", "facebook")
        self.mo.suggest("affiliate", "facebook")
        assert len(self.mo.get_by_type("ad_placement")) == 1

    def test_stats(self):
        self.mo.suggest("ad", "facebook")
        stats = self.mo.get_stats()
        assert stats["total_strategies"] == 1


# ─── FinancialMemory Tests ─────────────────────────────────────
class TestFinancialMemory:
    def setup_method(self):
        self.fm = FinancialMemory()

    def test_store(self):
        entry = self.fm.store("campaign", "summer_sale",
                               {"revenue": 5000, "roi": 2.5}, confidence=0.9)
        assert entry.entry_id.startswith("fmem_")
        assert entry.data["revenue"] == 5000

    def test_store_with_tags(self):
        entry = self.fm.store("strategy", "pricing", {}, tags=["successful", "tested"])
        assert "successful" in entry.tags

    def test_search_by_category(self):
        self.fm.store("campaign", "a", {})
        self.fm.store("strategy", "b", {})
        campaigns = self.fm.search(category="campaign")
        assert len(campaigns) == 1

    def test_search_by_key(self):
        self.fm.store("campaign", "summer_sale", {})
        self.fm.store("campaign", "winter_sale", {})
        results = self.fm.search(key="summer")
        assert len(results) == 1

    def test_search_by_tag(self):
        self.fm.store("a", "b", {}, tags=["viral"])
        results = self.fm.search(tag="viral")
        assert len(results) == 1

    def test_search_min_confidence(self):
        self.fm.store("a", "high", {}, confidence=0.9)
        self.fm.store("a", "low", {}, confidence=0.1)
        results = self.fm.search(min_confidence=0.5)
        assert len(results) == 1

    def test_get_successful(self):
        self.fm.store("a", "b", {}, confidence=0.9)
        self.fm.store("a", "c", {}, confidence=0.2)
        assert len(self.fm.get_successful()) == 1

    def test_get_failed(self):
        self.fm.store("a", "b", {}, confidence=0.1)
        self.fm.store("a", "c", {}, confidence=0.9)
        assert len(self.fm.get_failed()) == 1

    def test_get_latest(self):
        self.fm.store("a", "first", {})
        self.fm.store("a", "second", {})
        latest = self.fm.get_latest("a", 1)
        assert latest[0].key == "second"

    def test_max_entries(self):
        fm = FinancialMemory(max_entries=3)
        for i in range(5):
            fm.store("a", f"key_{i}", {})
        assert len(fm._entries) == 3

    def test_stats(self):
        self.fm.store("campaign", "a", {})
        self.fm.store("strategy", "b", {})
        stats = self.fm.get_stats()
        assert stats["total"] == 2
        assert stats["by_category"]["campaign"] == 1


# ─── BusinessMetrics Tests ─────────────────────────────────────
class TestBusinessMetrics:
    def setup_method(self):
        self.bm = BusinessMetrics()

    def test_record(self):
        entry = self.bm.record(revenue_growth=0.15, profit=5000,
                                conversion_rate=0.03, arpu=25.0)
        assert entry["revenue_growth"] == 0.15
        assert entry["arpu"] == 25.0

    def test_get_latest(self):
        self.bm.record(revenue_growth=0.1)
        self.bm.record(revenue_growth=0.2)
        latest = self.bm.get_latest()
        assert latest["revenue_growth"] == 0.2

    def test_get_latest_empty(self):
        assert self.bm.get_latest() == {}

    def test_get_average(self):
        self.bm.record(revenue_growth=0.1, arpu=10)
        self.bm.record(revenue_growth=0.3, arpu=20)
        avg = self.bm.get_average()
        assert avg["revenue_growth"] == 0.2
        assert avg["arpu"] == 15.0

    def test_get_average_empty(self):
        assert self.bm.get_average() == {}

    def test_get_trend(self):
        for i in range(5):
            self.bm.record(revenue_growth=i * 0.1)
        trend = self.bm.get_trend("revenue_growth", 3)
        assert len(trend) == 3

    def test_get_growth_direction_improving(self):
        self.bm.record(revenue_growth=0.1)
        self.bm.record(revenue_growth=0.2)
        assert self.bm.get_growth_direction() == "improving"

    def test_get_growth_direction_declining(self):
        self.bm.record(revenue_growth=0.3)
        self.bm.record(revenue_growth=0.1)
        assert self.bm.get_growth_direction() == "declining"

    def test_get_growth_direction_stable(self):
        self.bm.record(revenue_growth=0.1)
        self.bm.record(revenue_growth=0.1)
        assert self.bm.get_growth_direction() == "stable"

    def test_get_growth_direction_insufficient(self):
        assert self.bm.get_growth_direction() == "insufficient_data"

    def test_get_summary(self):
        self.bm.record(revenue_growth=0.1)
        summary = self.bm.get_summary()
        assert summary["total_records"] == 1
        assert "latest" in summary
        assert "average" in summary


# ─── BusinessReport Tests ──────────────────────────────────────
class TestBusinessReportGenerator:
    def setup_method(self):
        self.rg = BusinessReportGenerator()

    def test_generate(self):
        report = self.rg.generate("daily", {"revenue": 1000})
        assert report.report_id.startswith("brep_")
        assert report.data["revenue"] == 1000

    def test_generate_invalid_type(self):
        report = self.rg.generate("invalid")
        assert report.report_type == "daily"

    def test_add_insight(self):
        report = self.rg.generate("daily")
        report.add_insight("Revenue up 15%")
        assert len(report.insights) == 1

    def test_add_recommendation(self):
        report = self.rg.generate("daily")
        report.add_recommendation("Increase ad spend")
        assert len(report.recommendations) == 1

    def test_export_json(self):
        report = self.rg.generate("daily", {"revenue": 1000})
        report.add_insight("Test")
        json_str = report.export_json()
        assert "brep_" in json_str
        assert "revenue" in json_str

    def test_export_markdown(self):
        report = self.rg.generate("daily")
        report.add_insight("Insight 1")
        report.add_recommendation("Rec 1")
        md = report.export_markdown()
        assert "# Business Report" in md
        assert "Insight 1" in md

    def test_generate_insight(self):
        report = self.rg.generate_insight("weekly", "Big insight")
        assert len(report.insights) == 1

    def test_generate_recommendation(self):
        report = self.rg.generate_recommendation("monthly", "Big rec")
        assert len(report.recommendations) == 1

    def test_get_recent(self):
        for i in range(5):
            self.rg.generate(f"report_{i}")
        recent = self.rg.get_recent(3)
        assert len(recent) == 3

    def test_get_by_type(self):
        self.rg.generate("daily")
        self.rg.generate("weekly")
        self.rg.generate("daily")
        assert len(self.rg.get_by_type("daily")) == 2

    def test_get_revenue_dashboard(self):
        report = self.rg.get_revenue_dashboard({"total_revenue": 5000})
        assert report.report_type == "revenue_dashboard"
        assert len(report.insights) == 1

    def test_stats(self):
        self.rg.generate("daily")
        stats = self.rg.get_stats()
        assert stats["total"] == 1

    def test_report_score(self):
        report = self.rg.generate("daily")
        report.score = 0.85
        d = report.to_dict()
        assert d["score"] == 0.85


# ─── BusinessIntelligenceAPI Tests ─────────────────────────────
class TestBusinessIntelligenceAPI:
    def setup_method(self):
        self.api = BusinessIntelligenceAPI()

    def test_get_revenue(self):
        self.api.revenue_tracker.record("ad_revenue", 1000, "facebook")
        rev = self.api.get_revenue("facebook")
        assert rev["total"] == 1000

    def test_get_roi(self):
        roi = self.api.get_roi("facebook")
        assert roi["roi"] == 0.0

    def test_get_roi_with_data(self):
        self.api.roi_analyzer.calculate("facebook", revenue=500, cost=200)
        roi = self.api.get_roi("facebook")
        assert roi["roi"] == 1.5

    def test_get_campaigns(self):
        self.api.campaign_manager.create("Test", budget=1000)
        campaigns = self.api.get_campaigns()
        assert len(campaigns) >= 1

    def test_get_budget_status(self):
        self.api.budget_planner.allocate("ai_api", 1000)
        status = self.api.get_budget_status()
        assert "total_remaining" in status

    def test_get_forecast(self):
        self.api.forecaster.forecast_revenue("next_month", 5000, 0.1)
        forecast = self.api.get_forecast("revenue")
        assert forecast["predicted_value"] > 0

    def test_get_growth_recommendations(self):
        recs = self.api.get_growth_recommendations()
        assert len(recs) >= 1

    def test_get_health(self):
        health = self.api.get_health()
        assert "revenue_tracker" in health
        assert "roi_analyzer" in health

    def test_to_dict(self):
        result = self.api.to_dict()
        assert "revenue" in result
        assert "recommendations" in result


# ─── BusinessOrchestrator Tests ────────────────────────────────
class TestBusinessOrchestrator:
    def setup_method(self):
        self.orch = BusinessOrchestrator()

    def test_start_stop(self):
        assert self.orch.start() is True
        assert self.orch._is_running is True
        assert self.orch.stop() is True
        assert self.orch._is_running is False

    def test_run_pipeline(self):
        results = self.orch.run_pipeline("facebook",
                                          {"ad_revenue": 1000, "affiliate": 500},
                                          {"cost": 300})
        assert "stages" in results
        assert "revenue" in results["stages"]
        assert "roi" in results["stages"]
        assert "forecast" in results["stages"]
        assert "duration_ms" in results

    def test_run_pipeline_empty(self):
        results = self.orch.run_pipeline("x")
        assert "stages" in results

    def test_health_check(self):
        health = self.orch.get_health()
        assert "revenue_tracker" in health
        assert "roi_analyzer" in health
        assert "campaign_manager" in health
        assert "budget_planner" in health
        assert "forecaster" in health
        assert "opportunity_detector" in health
        assert "financial_memory" in health
        assert "is_running" in health

    def test_get_api(self):
        api = self.orch.get_api()
        assert isinstance(api, BusinessIntelligenceAPI)

    def test_pipeline_runs_tracked(self):
        self.orch.run_pipeline("facebook")
        self.orch.run_pipeline("x")
        assert len(self.orch._pipeline_runs) == 2

    def test_revenue_tracking(self):
        self.orch.run_pipeline("facebook", {"ad_revenue": 500})
        total = self.orch.revenue_tracker.get_total_revenue("facebook")
        assert total == 500

    def test_roi_tracking(self):
        self.orch.run_pipeline("facebook",
                                {"ad_revenue": 1000},
                                {"cost": 500})
        latest = self.orch.roi_analyzer.get_latest("facebook")
        assert latest is not None
        assert latest.roi == 1.0


# ─── Exceptions Tests ──────────────────────────────────────────
class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(RevenueError, BusinessError)
        assert issubclass(ROIError, BusinessError)
        assert issubclass(CampaignError, BusinessError)
        assert issubclass(BudgetError, BusinessError)
        assert issubclass(ForecastError, BusinessError)
        assert issubclass(OpportunityError, BusinessError)
        assert issubclass(FinancialMemoryError, BusinessError)

    def test_base_is_exception(self):
        assert issubclass(BusinessError, Exception)

    def test_can_be_raised(self):
        try:
            raise RevenueError("Revenue tracking failed")
        except BusinessError as e:
            assert "Revenue tracking failed" in str(e)
