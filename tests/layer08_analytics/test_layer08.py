"""Tests for Layer 8 Analytics — All modules."""
import time
from layers.layer08_analytics.modules.data_collector.collector import DataCollector, DataSource, DataPoint
from layers.layer08_analytics.modules.metric_engine.metrics import MetricEngine, MetricDefinition, MetricValue
from layers.layer08_analytics.modules.report_generator.reports import ReportGenerator, AnalyticsReport, ReportSection
from layers.layer08_analytics.modules.performance_analyzer.analyzer import PerformanceAnalyzer, PerformanceDimension
from layers.layer08_analytics.modules.trend_detector.detector import TrendDetector
from layers.layer08_analytics.modules.ab_test_engine.engine import ABTestEngine, ABTest, ABVariant
from layers.layer08_analytics.modules.funnel_analyzer.analyzer import FunnelAnalyzer, FunnelStep
from layers.layer08_analytics.modules.attribution_engine.attribution import AttributionEngine, AttributionTouchpoint
from layers.layer08_analytics.modules.dashboard_service.dashboard import DashboardService, DashboardWidget, DashboardLayout
from layers.layer08_analytics.modules.analytics_orchestrator.orchestrator import AnalyticsOrchestrator
from layers.layer08_analytics.modules.exceptions import AnalyticsError, DataCollectionError, MetricCalculationError, ReportGenerationError, InsightError


# ═══ Module 1: Data Collector ═══
class TestDataPoint:
    def test_create(self):
        dp = DataPoint("source1", "views", 100.0)
        assert dp.source == "source1"
        assert dp.value == 100.0
    def test_to_dict(self):
        dp = DataPoint("src", "metric", 42.0)
        d = dp.to_dict()
        assert d["source"] == "src"
        assert d["value"] == 42.0

class TestDataSource:
    def test_create(self):
        ds = DataSource("s1", "Test Source")
        assert ds.enabled is True
    def test_is_ready(self):
        ds = DataSource("s1", "Test")
        ds.last_fetched = time.time() - 10
        ds.interval_seconds = 5
        assert ds.is_ready() is True

class TestDataCollector:
    def setup_method(self):
        self.dc = DataCollector()
    def test_register_source(self):
        ds = DataSource("s1", "Test")
        self.dc.register_source(ds)
        assert self.dc.get_source("s1") is not None
    def test_unregister_source(self):
        self.dc.register_source(DataSource("s1", "Test"))
        assert self.dc.unregister_source("s1") is True
        assert self.dc.unregister_source("missing") is False
    def test_collect_manual(self):
        dp = self.dc.collect_manual("src", "views", 100.0, platform="fb")
        assert dp.value == 100.0
        assert dp.dimensions["platform"] == "fb"
    def test_collect_with_fetcher(self):
        ds = DataSource("s1", "Test", lambda: {"views": 100, "likes": 50})
        self.dc.register_source(ds)
        points = self.dc.collect("s1")
        assert len(points) == 2
    def test_collect_disabled(self):
        ds = DataSource("s1", "Test", lambda: {"views": 100})
        ds.enabled = False
        self.dc.register_source(ds)
        assert self.dc.collect("s1") == []
    def test_collect_all(self):
        self.dc.register_source(DataSource("s1", "A", lambda: {"x": 1}))
        self.dc.register_source(DataSource("s2", "B", lambda: {"y": 2}))
        points = self.dc.collect_all()
        assert len(points) == 2
    def test_get_data(self):
        self.dc.collect_manual("src", "views", 100)
        self.dc.collect_manual("src", "likes", 50)
        assert len(self.dc.get_data("src")) == 2
    def test_get_ready_sources(self):
        ds = DataSource("s1", "Test")
        ds.last_fetched = 0
        ds.interval_seconds = 1
        self.dc.register_source(ds)
        ready = self.dc.get_ready_sources()
        assert len(ready) == 1
    def test_total_points(self):
        self.dc.collect_manual("src", "x", 1)
        assert self.dc.total_points == 1

# ═══ Module 2: Metric Engine ═══
class TestMetricDefinition:
    def test_create(self):
        md = MetricDefinition("m1", "Views", "sum")
        assert md.metric_id == "m1"
    def test_to_dict(self):
        d = MetricDefinition("m1", "Views", "sum").to_dict()
        assert d["name"] == "Views"

class TestMetricValue:
    def test_create(self):
        mv = MetricValue("m1", 42.0)
        assert mv.value == 42.0

class TestMetricEngine:
    def setup_method(self):
        self.me = MetricEngine()
    def test_define(self):
        self.me.define(MetricDefinition("views", "Views", "sum"))
        assert self.me.get_definition("views") is not None
    def test_calculate_sum(self):
        self.me.define(MetricDefinition("m1", "M", "sum"))
        result = self.me.calculate("m1", [1, 2, 3, 4])
        assert result.value == 10.0
    def test_calculate_avg(self):
        self.me.define(MetricDefinition("m1", "M", "avg"))
        result = self.me.calculate("m1", [10, 20, 30])
        assert result.value == 20.0
    def test_calculate_median(self):
        self.me.define(MetricDefinition("m1", "M", "median"))
        result = self.me.calculate("m1", [1, 3, 5, 7, 9])
        assert result.value == 5.0
    def test_calculate_std_dev(self):
        self.me.define(MetricDefinition("m1", "M", "std_dev"))
        result = self.me.calculate("m1", [2, 4, 4, 4, 5, 5, 7, 9])
        assert result.value > 0
    def test_calculate_p95(self):
        self.me.define(MetricDefinition("m1", "M", "p95"))
        result = self.me.calculate("m1", list(range(100)))
        assert result.value >= 90
    def test_calculate_growth_rate(self):
        self.me.define(MetricDefinition("m1", "M", "growth_rate"))
        result = self.me.calculate("m1", [100, 120])
        assert result.value == 20.0
    def test_calculate_empty(self):
        result = self.me.calculate("m1", [])
        assert result.value == 0.0
    def test_get_recent_values(self):
        self.me.define(MetricDefinition("m1", "M", "sum"))
        self.me.calculate("m1", [1])
        self.me.calculate("m1", [2])
        recent = self.me.get_recent_values("m1")
        assert len(recent) == 2

# ═══ Module 3: Report Generator ═══
class TestReportSection:
    def test_create(self):
        rs = ReportSection("Key Metrics", 1)
        assert rs.title == "Key Metrics"
    def test_add_metric(self):
        rs = ReportSection()
        rs.add_metric("views", 1000, "count")
        assert len(rs.metrics) == 1
    def test_to_dict(self):
        d = ReportSection("Test", 1).to_dict()
        assert d["title"] == "Test"

class TestAnalyticsReport:
    def test_create(self):
        r = AnalyticsReport("Weekly Report")
        assert r.report_id.startswith("rpt_")
    def test_add_section(self):
        r = AnalyticsReport()
        r.add_section(ReportSection("S1", 1))
        assert len(r.sections) == 1
    def test_get_section(self):
        r = AnalyticsReport()
        r.add_section(ReportSection("Metrics", 1))
        assert r.get_section("Metrics") is not None
        assert r.get_section("Missing") is None

class TestReportGenerator:
    def setup_method(self):
        self.rg = ReportGenerator()
    def test_generate_summary(self):
        report = self.rg.generate_summary_report("Weekly", {"views": 1000, "likes": 50})
        assert report.title == "Weekly"
        assert len(report.sections) == 2
    def test_generate_comparison(self):
        report = self.rg.generate_comparison_report("Compare", {"views": 1000}, {"views": 800})
        assert report.title == "Compare"
    def test_get_reports(self):
        self.rg.generate_summary_report("R1", {"x": 1})
        self.rg.generate_summary_report("R2", {"y": 2})
        assert len(self.rg.get_reports()) == 2

# ═══ Module 4: Performance Analyzer ═══
class TestPerformanceDimension:
    def test_create(self):
        pd = PerformanceDimension("eng", "engagement_rate")
        assert pd.dimension_id == "eng"
    def test_add_datapoint(self):
        pd = PerformanceDimension("eng", "engagement_rate")
        pd.add_datapoint(5.0)
        assert pd.count == 1
    def test_mean(self):
        pd = PerformanceDimension("eng", "engagement_rate")
        for v in [1, 2, 3, 4, 5]:
            pd.add_datapoint(v)
        assert pd.mean == 3.0
    def test_trend_improving(self):
        pd = PerformanceDimension("eng", "engagement_rate")
        for v in [1, 2, 3, 4, 5, 6, 7]:
            pd.add_datapoint(v)
        assert pd.trend == "improving"
    def test_trend_stable(self):
        pd = PerformanceDimension("eng", "engagement_rate")
        for _ in range(10):
            pd.add_datapoint(5.0)
        assert pd.trend == "stable"

class TestPerformanceAnalyzer:
    def setup_method(self):
        self.pa = PerformanceAnalyzer()
    def test_add_and_analyze(self):
        dim = PerformanceDimension("eng", "engagement_rate")
        for v in [1, 2, 3, 4, 5]:
            dim.add_datapoint(v)
        self.pa.add_dimension(dim)
        result = self.pa.analyze("eng")
        assert result is not None
        assert result.score == 3.0
    def test_analyze_all(self):
        dim = PerformanceDimension("eng", "engagement_rate")
        dim.add_datapoint(5.0)
        self.pa.add_dimension(dim)
        results = self.pa.analyze_all()
        assert len(results) == 1
    def test_analyze_empty(self):
        assert self.pa.analyze("missing") is None

# ═══ Module 5: Trend Detector ═══
class TestTrendDetector:
    def setup_method(self):
        self.td = TrendDetector()
    def test_add_datapoint(self):
        self.td.add_datapoint("views", 100)
        assert len(self.td.get_series("views")) == 1
    def test_add_batch(self):
        self.td.add_batch("views", [1, 2, 3, 4, 5])
        assert len(self.td.get_series("views")) == 5
    def test_detect_up(self):
        self.td.add_batch("views", [10, 20, 30, 40, 50])
        trend = self.td.detect("views")
        assert trend is not None
        assert trend.direction == "up"
    def test_detect_down(self):
        self.td.add_batch("views", [50, 40, 30, 20, 10])
        trend = self.td.detect("views")
        assert trend.direction == "down"
    def test_detect_stable(self):
        self.td.add_batch("views", [100, 100, 100, 100, 100])
        trend = self.td.detect("views")
        assert trend.direction == "stable"
    def test_detect_insufficient_data(self):
        self.td.add_batch("views", [1, 2])
        assert self.td.detect("views") is None
    def test_anomaly_detection(self):
        self.td.add_batch("views", [10, 10, 10, 10, 10, 10, 10, 500, 10, 10])
        trend = self.td.detect("views")
        assert trend is not None
        assert len(trend.anomalies) >= 1

# ═══ Module 6: A/B Test Engine ═══
class TestABVariant:
    def test_create(self):
        v = ABVariant("v1", "Control")
        assert v.variant_id == "v1"
    def test_conversion_rate(self):
        v = ABVariant("v1", "Control")
        v.impressions = 1000
        v.conversions = 50
        assert v.conversion_rate == 5.0

class TestABTest:
    def test_create(self):
        t = ABTest("t1", "Test 1")
        assert t.status == "draft"

class TestABTestEngine:
    def setup_method(self):
        self.engine = ABTestEngine()
    def test_create_test(self):
        test = self.engine.create_test("t1", "Headline Test", ["Control", "Variant"])
        assert test.status == "draft"
        assert len(test.variants) == 2
    def test_start_test(self):
        self.engine.create_test("t1", "Test", ["A", "B"])
        assert self.engine.start_test("t1") is True
    def test_record_impression(self):
        test = self.engine.create_test("t1", "Test", ["A", "B"])
        variant = test.variants[0]
        assert self.engine.record_impression("t1", variant.variant_id) is True
    def test_record_conversion(self):
        test = self.engine.create_test("t1", "Test", ["A", "B"])
        variant = test.variants[0]
        assert self.engine.record_conversion("t1", variant.variant_id, 10.0) is True
    def test_analyze(self):
        test = self.engine.create_test("t1", "Test", ["Control", "Variant"])
        for _ in range(100):
            self.engine.record_impression("t1", test.variants[0].variant_id)
            self.engine.record_impression("t1", test.variants[1].variant_id)
        for _ in range(10):
            self.engine.record_conversion("t1", test.variants[0].variant_id)
        for _ in range(20):
            self.engine.record_conversion("t1", test.variants[1].variant_id)
        result = self.engine.analyze("t1")
        assert result is not None
        assert result.winner != ""

# ═══ Module 7: Funnel Analyzer ═══
class TestFunnelStep:
    def test_create(self):
        fs = FunnelStep("s1", "Landing", 0)
        assert fs.step_id == "s1"
    def test_conversion_rate(self):
        fs = FunnelStep("s1", "Landing", 0)
        fs.entries = 1000
        fs.conversions = 50
        assert fs.conversion_rate == 5.0

class TestFunnelAnalyzer:
    def setup_method(self):
        self.fa = FunnelAnalyzer()
    def test_create_funnel(self):
        funnel = self.fa.create_funnel("f1", "Conversion", ["Landing", "Signup", "Purchase"])
        assert len(funnel.steps) == 3
    def test_update_step(self):
        self.fa.create_funnel("f1", "Test", ["A", "B"])
        assert self.fa.update_step("f1", "f1_s0", 1000, 800, 100) is True
    def test_analyze(self):
        self.fa.create_funnel("f1", "Test", ["Landing", "Signup", "Purchase"])
        self.fa.update_step("f1", "f1_s0", 1000, 500, 0)
        self.fa.update_step("f1", "f1_s1", 500, 200, 0)
        self.fa.update_step("f1", "f1_s2", 200, 200, 50)
        result = self.fa.analyze("f1")
        assert result is not None
        assert result.total_entries == 1000
        assert result.total_conversions == 50

# ═══ Module 8: Attribution Engine ═══
class TestAttributionTouchpoint:
    def test_create(self):
        tp = AttributionTouchpoint("facebook", "c1")
        assert tp.channel == "facebook"
    def test_to_dict(self):
        d = AttributionTouchpoint("fb", "c1").to_dict()
        assert d["channel"] == "fb"

class TestAttributionEngine:
    def setup_method(self):
        self.ae = AttributionEngine()
    def test_add_touchpoint(self):
        tp = AttributionTouchpoint("facebook", "c1")
        self.ae.add_touchpoint("user1", tp)
        assert len(self.ae.get_touchpoints("user1")) == 1
    def test_analyze_first_touch(self):
        self.ae.add_touchpoint("u1", AttributionTouchpoint("facebook"))
        self.ae.add_touchpoint("u1", AttributionTouchpoint("google"))
        results = self.ae.analyze_first_touch()
        assert len(results) >= 1
    def test_analyze_linear(self):
        self.ae.add_touchpoint("u1", AttributionTouchpoint("facebook"))
        self.ae.add_touchpoint("u1", AttributionTouchpoint("google"))
        results = self.ae.analyze_linear()
        assert len(results) >= 1

# ═══ Module 9: Dashboard Service ═══
class TestDashboardWidget:
    def test_create(self):
        w = DashboardWidget("w1", "metric")
        assert w.widget_id == "w1"
    def test_is_stale(self):
        w = DashboardWidget("w1")
        w.last_updated = 0
        assert w.is_stale() is True

class TestDashboardLayout:
    def test_create(self):
        dl = DashboardLayout("d1", "Main Dashboard")
        assert dl.layout_id == "d1"
    def test_add_widget(self):
        dl = DashboardLayout("d1", "Main")
        dl.add_widget(DashboardWidget("w1", "metric"))
        assert len(dl.widgets) == 1

class TestDashboardService:
    def setup_method(self):
        self.ds = DashboardService()
    def test_create_layout(self):
        layout = self.ds.create_layout("d1", "Main")
        assert layout.layout_id == "d1"
    def test_add_widget(self):
        self.ds.create_layout("d1", "Main")
        w = DashboardWidget("w1", "metric")
        assert self.ds.add_widget("d1", w) is True
    def test_take_snapshot(self):
        self.ds.create_layout("d1", "Main")
        snap = self.ds.take_snapshot("d1", {"views": 100})
        assert snap is not None
        assert snap.widgets_data["views"] == 100
    def test_get_latest_snapshot(self):
        self.ds.create_layout("d1", "Main")
        self.ds.take_snapshot("d1", {"v1": 1})
        self.ds.take_snapshot("d1", {"v2": 2})
        latest = self.ds.get_latest_snapshot("d1")
        assert latest.widgets_data["v2"] == 2
    def test_serving_count(self):
        self.ds.create_layout("d1", "Main")
        self.ds.take_snapshot("d1", {"v": 1})
        assert self.ds.serving_count == 1

# ═══ Module 10: Analytics Orchestrator ═══
class TestAnalyticsOrchestrator:
    def setup_method(self):
        self.orch = AnalyticsOrchestrator()
    def test_run_pipeline(self):
        result = self.orch.run_pipeline()
        assert result.pipeline_id.startswith("ap_")
        assert result.duration_ms >= 0
    def test_run_pipeline_with_data(self):
        self.orch.collector.register_source(DataSource("s1", "Test", lambda: {"views": 100}))
        self.orch.trend_detector.add_batch("views", [10, 20, 30, 40, 50])
        result = self.orch.run_pipeline()
        assert result.trends_detected >= 1
    def test_health(self):
        self.orch.run_pipeline()
        health = self.orch.get_health()
        assert health["pipeline_runs"] >= 1
    def test_events_tracked(self):
        self.orch.run_pipeline()
        assert len(self.orch.events) >= 1

# ═══ Exceptions ═══
class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(DataCollectionError, AnalyticsError)
        assert issubclass(MetricCalculationError, AnalyticsError)
        assert issubclass(ReportGenerationError, AnalyticsError)
        assert issubclass(InsightError, AnalyticsError)
    def test_message(self):
        err = DataCollectionError("failed to collect")
        assert str(err) == "failed to collect"
