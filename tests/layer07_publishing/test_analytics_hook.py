"""Tests for Layer 7 Module 7 — Analytics Hook."""
from layers.layer07_publishing.modules.analytics_hook.analytics_event import AnalyticsEvent
from layers.layer07_publishing.modules.analytics_hook.metrics_collector import MetricsCollector
from layers.layer07_publishing.modules.analytics_hook.metrics_normalizer import MetricsNormalizer
from layers.layer07_publishing.modules.analytics_hook.engagement_analyzer import EngagementAnalyzer
from layers.layer07_publishing.modules.analytics_hook.reach_analyzer import ReachAnalyzer
from layers.layer07_publishing.modules.analytics_hook.conversion_tracker import ConversionTracker
from layers.layer07_publishing.modules.analytics_hook.trend_tracker import TrendTracker, TrendDataPoint, TrendResult
from layers.layer07_publishing.modules.analytics_hook.analytics_memory import AnalyticsMemory, HistoricalRecord
from layers.layer07_publishing.modules.analytics_hook.performance_scorer import PerformanceScorer
from layers.layer07_publishing.modules.analytics_hook.analytics_manager import AnalyticsManager, AnalyticsReport
from layers.layer07_publishing.modules.analytics_hook.exceptions import (
    AnalyticsError, FetchError, NormalizationError,
)


# ─── AnalyticsEvent Tests ────────────────────────────────────────────
class TestAnalyticsEvent:
    def test_create(self):
        e = AnalyticsEvent("facebook", "post_1", "c_1")
        assert e.event_id.startswith("evt_")
        assert e.platform == "facebook"
        assert e.post_id == "post_1"
        assert e.content_id == "c_1"

    def test_get_set_metric(self):
        e = AnalyticsEvent()
        e.set_metric("likes", 42)
        assert e.get("likes") == 42.0
        assert e.get("missing", 0.0) == 0.0

    def test_merge(self):
        e1 = AnalyticsEvent()
        e1.set_metric("likes", 10)
        e2 = AnalyticsEvent()
        e2.set_metric("comments", 5)
        e1.merge(e2)
        assert e1.get("likes") == 10
        assert e1.get("comments") == 5

    def test_to_dict(self):
        e = AnalyticsEvent("fb", "p1")
        e.set_metric("likes", 10)
        d = e.to_dict()
        assert d["platform"] == "fb"
        assert d["metrics"]["likes"] == 10


# ─── MetricsCollector Tests ──────────────────────────────────────────
class TestMetricsCollector:
    def setup_method(self):
        self.mc = MetricsCollector()

    def test_collect_single(self):
        def fetcher(platform, post_id):
            return {"likes": 10, "comments": 5, "engagement": {"shares": 3}}
        event = self.mc.collect_single("facebook", "p1", fetcher)
        assert event is not None
        assert event.platform == "facebook"
        assert event.get("likes") == 10
        assert self.mc.collection_count == 1

    def test_collect_single_exception(self):
        def bad_fetcher(p, pid):
            raise RuntimeError("API error")
        try:
            self.mc.collect_single("fb", "p1", bad_fetcher)
            assert False
        except FetchError:
            pass

    def test_collect_batch(self):
        posts = [
            {"platform": "fb", "post_id": "p1"},
            {"platform": "li", "post_id": "p2"},
        ]
        def fetcher(p, pid):
            return {"likes": 5}
        events = self.mc.collect_batch(posts, fetcher)
        assert len(events) == 2

    def test_collect_batch_empty(self):
        events = self.mc.collect_batch([], lambda p, pid: {})
        assert events == []

    def test_flatten_metrics(self):
        flat = self.mc._flatten_metrics({"a": 1, "b": {"c": 2, "d": "text"}, "e": "hello"})
        assert flat["a"] == 1
        assert flat["c"] == 2
        assert flat["e"] == "hello"

    def test_avg_fetch_time(self):
        self.mc.collect_single("fb", "p1", lambda p, pid: {"x": 1})
        assert self.mc.avg_fetch_time_ms >= 0


# ─── MetricsNormalizer Tests ─────────────────────────────────────────
class TestMetricsNormalizer:
    def setup_method(self):
        self.norm = MetricsNormalizer()

    def test_normalize_facebook(self):
        e = AnalyticsEvent("facebook", "p1")
        e.metrics = {"reactions": 10, "comments": 5, "post_impressions": 1000}
        self.norm.normalize(e)
        assert e.metrics["likes"] == 10
        assert e.metrics["impressions"] == 1000

    def test_normalize_instagram(self):
        e = AnalyticsEvent("instagram", "p1")
        e.metrics = {"like_count": 20, "comments_count": 8}
        self.norm.normalize(e)
        assert e.metrics["likes"] == 20
        assert e.metrics["comments"] == 8

    def test_normalize_twitter(self):
        e = AnalyticsEvent("twitter", "p1")
        e.metrics = {"favorite_count": 15, "retweet_count": 7}
        self.norm.normalize(e)
        assert e.metrics["likes"] == 15
        assert e.metrics["shares"] == 7

    def test_normalize_unknown_platform(self):
        e = AnalyticsEvent("unknown_platform", "p1")
        e.metrics = {"likes": 10}
        self.norm.normalize(e)
        assert e.metrics["likes"] == 10

    def test_normalize_batch(self):
        events = [
            AnalyticsEvent("facebook", "p1"),
            AnalyticsEvent("instagram", "p2"),
        ]
        events[0].metrics = {"reactions": 5}
        events[1].metrics = {"like_count": 10}
        self.norm.normalize_batch(events)
        assert events[0].metrics.get("likes") == 5
        assert events[1].metrics.get("likes") == 10

    def test_get_platform_mapping(self):
        mapping = self.norm.get_platform_mapping("facebook")
        assert "reactions" in mapping

    def test_supported_platforms(self):
        platforms = self.norm.supported_platforms()
        assert "facebook" in platforms
        assert "instagram" in platforms

    def test_compute_engagement_rate(self):
        e = AnalyticsEvent("fb", "p1")
        e.metrics = {"likes": 10, "comments": 5, "shares": 3, "reach": 1000}
        rate = self.norm.compute_engagement_rate(e)
        assert rate == 1.8

    def test_normalization_count(self):
        self.norm.normalize(AnalyticsEvent("fb", "p1"))
        assert self.norm.normalization_count == 1


# ─── EngagementAnalyzer Tests ────────────────────────────────────────
class TestEngagementAnalyzer:
    def setup_method(self):
        self.ea = EngagementAnalyzer()

    def test_analyze(self):
        e = AnalyticsEvent("fb", "p1")
        e.metrics = {"likes": 10, "comments": 5, "shares": 3, "saves": 2, "reach": 1000}
        bd = self.ea.analyze(e)
        assert bd.total_engagement == 20
        assert bd.engagement_rate == 2.0
        assert bd.engagement_score > 0

    def test_analyze_empty(self):
        e = AnalyticsEvent("fb", "p1")
        bd = self.ea.analyze(e)
        assert bd.total_engagement == 0
        assert bd.engagement_rate == 0.0

    def test_analyze_batch(self):
        events = [AnalyticsEvent("fb", f"p{i}") for i in range(3)]
        results = self.ea.analyze_batch(events)
        assert len(results) == 3

    def test_get_top_engaged(self):
        events = []
        for i in range(5):
            e = AnalyticsEvent("fb", f"p{i}")
            e.metrics = {"likes": i * 10, "reach": 1000}
            events.append(e)
        top = self.ea.get_top_engaged(events, top_n=2)
        assert len(top) == 2
        assert top[0].post_id == "p4"

    def test_weights(self):
        e = AnalyticsEvent("fb", "p1")
        e.metrics = {"likes": 1, "comments": 1, "shares": 1, "saves": 1, "reach": 1000}
        bd = self.ea.analyze(e)
        assert bd.engagement_score == 13.0  # 1+3+5+4

    def test_analysis_count(self):
        self.ea.analyze(AnalyticsEvent("fb", "p1"))
        assert self.ea.analysis_count == 1


# ─── ReachAnalyzer Tests ─────────────────────────────────────────────
class TestReachAnalyzer:
    def setup_method(self):
        self.ra = ReachAnalyzer()

    def test_analyze(self):
        e = AnalyticsEvent("fb", "p1")
        e.metrics = {"reach": 5000, "impressions": 8000, "views": 3000}
        bd = self.ra.analyze(e)
        assert bd.reach == 5000
        assert bd.impressions == 8000
        assert bd.frequency == 1.6

    def test_analyze_empty(self):
        e = AnalyticsEvent("fb", "p1")
        bd = self.ra.analyze(e)
        assert bd.reach == 0
        assert bd.frequency == 0

    def test_analyze_batch(self):
        events = [AnalyticsEvent("fb", f"p{i}") for i in range(3)]
        results = self.ra.analyze_batch(events)
        assert len(results) == 3

    def test_total_reach(self):
        events = [AnalyticsEvent("fb", f"p{i}") for i in range(3)]
        events[0].metrics = {"reach": 1000}
        events[1].metrics = {"reach": 2000}
        assert self.ra.total_reach(events) == 3000

    def test_total_views(self):
        events = [AnalyticsEvent("fb", f"p{i}") for i in range(3)]
        events[0].metrics = {"views": 500}
        events[1].metrics = {"views": 1500}
        assert self.ra.total_views(events) == 2000

    def test_avg_completion_rate(self):
        e1 = AnalyticsEvent("fb", "p1")
        e1.metrics = {"completion_rate": 0.8}
        e2 = AnalyticsEvent("fb", "p2")
        e2.metrics = {"completion_rate": 0.6}
        avg = self.ra.avg_completion_rate([e1, e2])
        assert avg == 0.7

    def test_analysis_count(self):
        self.ra.analyze(AnalyticsEvent("fb", "p1"))
        assert self.ra.analysis_count == 1


# ─── ConversionTracker Tests ─────────────────────────────────────────
class TestConversionTracker:
    def setup_method(self):
        self.ct = ConversionTracker()

    def test_track(self):
        e = AnalyticsEvent("fb", "p1")
        e.metrics = {"link_clicks": 50, "impressions": 2000, "signups": 5, "revenue": 100, "cost": 50}
        bd = self.ct.track(e)
        assert bd.link_clicks == 50
        assert bd.ctr == 2.5
        assert bd.signups == 5
        assert bd.roas == 2.0

    def test_track_empty(self):
        e = AnalyticsEvent("fb", "p1")
        bd = self.ct.track(e)
        assert bd.link_clicks == 0
        assert bd.roas == 0.0

    def test_track_batch(self):
        events = [AnalyticsEvent("fb", f"p{i}") for i in range(3)]
        results = self.ct.track_batch(events)
        assert len(results) == 3

    def test_total_revenue(self):
        e1 = AnalyticsEvent("fb", "p1")
        e1.metrics = {"revenue": 100}
        e2 = AnalyticsEvent("fb", "p2")
        e2.metrics = {"revenue": 200}
        assert self.ct.total_revenue([e1, e2]) == 300

    def test_total_clicks(self):
        e1 = AnalyticsEvent("fb", "p1")
        e1.metrics = {"clicks": 50}
        assert self.ct.total_clicks([e1]) == 50

    def test_tracking_count(self):
        self.ct.track(AnalyticsEvent("fb", "p1"))
        assert self.ct.tracking_count == 1


# ─── TrendTracker Tests ──────────────────────────────────────────────
class TestTrendDataPoint:
    def test_create(self):
        dp = TrendDataPoint(42.0, "likes")
        assert dp.value == 42.0
        assert dp.label == "likes"

    def test_to_dict(self):
        dp = TrendDataPoint(42.0, "likes")
        d = dp.to_dict()
        assert d["value"] == 42.0


class TestTrendResult:
    def test_create(self):
        tr = TrendResult()
        assert tr.trend_direction == "stable"
        assert tr.is_viral is False

    def test_to_dict(self):
        tr = TrendResult()
        tr.trend_direction = "up"
        d = tr.to_dict()
        assert d["trend_direction"] == "up"


class TestTrendTracker:
    def setup_method(self):
        self.tt = TrendTracker()

    def test_record(self):
        dp = self.tt.record("p1", 10, "day1")
        assert dp.value == 10
        history = self.tt.get_history("p1")
        assert len(history) == 1

    def test_record_multiple(self):
        for i in range(5):
            self.tt.record("p1", i * 10)
        assert len(self.tt.get_history("p1")) == 5

    def test_analyze_up(self):
        for i in range(10):
            self.tt.record("p1", i * 100)
        result = self.tt.analyze("p1")
        assert result.trend_direction == "up"
        assert result.growth_rate > 0

    def test_analyze_down(self):
        values = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
        for v in values:
            self.tt.record("p1", v)
        result = self.tt.analyze("p1")
        assert result.trend_direction == "down"

    def test_analyze_stable(self):
        for _ in range(10):
            self.tt.record("p1", 100)
        result = self.tt.analyze("p1")
        assert result.trend_direction == "stable"

    def test_analyze_single_point(self):
        self.tt.record("p1", 50)
        result = self.tt.analyze("p1")
        assert result.data_points_count == 1
        assert result.peak_value == 50

    def test_analyze_empty(self):
        result = self.tt.analyze("nonexistent")
        assert result.data_points_count == 0

    def test_peak_detection(self):
        for v in [10, 20, 50, 30, 10]:
            self.tt.record("p1", v)
        result = self.tt.analyze("p1")
        assert result.peak_value == 50

    def test_get_all_post_ids(self):
        self.tt.record("p1", 10)
        self.tt.record("p2", 20)
        ids = self.tt.get_all_post_ids()
        assert "p1" in ids
        assert "p2" in ids

    def test_tracking_count(self):
        self.tt.record("p1", 10)
        self.tt.record("p1", 20)
        self.tt.analyze("p1")
        assert self.tt.tracking_count == 1


# ─── AnalyticsMemory Tests ───────────────────────────────────────────
class TestHistoricalRecord:
    def test_create(self):
        r = HistoricalRecord("p1", "fb", {"likes": 10})
        assert r.post_id == "p1"
        assert r.platform == "fb"

    def test_to_dict(self):
        r = HistoricalRecord("p1", "fb", {"likes": 10})
        d = r.to_dict()
        assert d["post_id"] == "p1"


class TestAnalyticsMemory:
    def setup_method(self):
        self.mem = AnalyticsMemory(max_records=100)

    def test_store(self):
        e = AnalyticsEvent("fb", "p1")
        e.metrics = {"likes": 10}
        rec = self.mem.store(e)
        assert rec.post_id == "p1"
        assert self.mem.record_count == 1

    def test_get_history(self):
        e = AnalyticsEvent("fb", "p1")
        e.metrics = {"likes": 10}
        self.mem.store(e)
        history = self.mem.get_history("p1")
        assert len(history) == 1

    def test_get_latest(self):
        e1 = AnalyticsEvent("fb", "p1")
        e1.metrics = {"likes": 10}
        self.mem.store(e1)
        e2 = AnalyticsEvent("fb", "p1")
        e2.metrics = {"likes": 20}
        self.mem.store(e2)
        latest = self.mem.get_latest("p1")
        assert latest is not None
        assert latest.metrics["likes"] == 20

    def test_get_latest_empty(self):
        assert self.mem.get_latest("nonexistent") is None

    def test_get_platform_history(self):
        self.mem.store(AnalyticsEvent("fb", "p1"))
        self.mem.store(AnalyticsEvent("li", "p2"))
        self.mem.store(AnalyticsEvent("fb", "p3"))
        fb_history = self.mem.get_platform_history("fb")
        assert len(fb_history) == 2

    def test_compare(self):
        e1 = AnalyticsEvent("fb", "p1")
        e1.metrics = {"likes": 10}
        self.mem.store(e1)
        e2 = AnalyticsEvent("fb", "p1")
        e2.metrics = {"likes": 25}
        self.mem.store(e2)
        changes = self.mem.compare("p1")
        assert changes is not None
        assert changes["likes"]["change"] == 15

    def test_compare_single(self):
        self.mem.store(AnalyticsEvent("fb", "p1"))
        assert self.mem.compare("p1") is None

    def test_max_records_overflow(self):
        for i in range(110):
            e = AnalyticsEvent("fb", f"p{i}")
            self.mem.store(e)
        assert self.mem.record_count <= 100


# ─── PerformanceScorer Tests ─────────────────────────────────────────
class TestPerformanceScorer:
    def setup_method(self):
        self.ps = PerformanceScorer()

    def test_score_high(self):
        result = self.ps.score(engagement_rate=10, reach=10000, ctr=5, growth_rate=80)
        assert result.score > 80
        assert result.grade in ("A+", "A", "A-")
        assert result.success_level in ("excellent", "good")

    def test_score_low(self):
        result = self.ps.score(engagement_rate=0.1, reach=50, ctr=0.1, growth_rate=0)
        assert result.score < 30
        assert result.grade in ("F", "D", "C")

    def test_score_empty(self):
        result = self.ps.score()
        assert result.score == 0.0
        assert result.grade == "F"

    def test_score_event(self):
        e = AnalyticsEvent("fb", "p1")
        e.metrics = {"engagement_rate": 5, "reach": 1000, "ctr": 3}
        result = self.ps.score_event(e)
        assert result.score > 0

    def test_grade_thresholds(self):
        # Test that the grade function maps correctly for known scores
        # All zeros should produce F
        result_f = self.ps.score(engagement_rate=0.0, reach=0, ctr=0.0, growth_rate=0)
        assert result_f.grade == "F"
        # Very high values should produce high grade
        result_high = self.ps.score(engagement_rate=10.0, reach=50000, ctr=10.0, growth_rate=100)
        assert result_high.grade in ("A+", "A", "A-")
        # The scorer's _get_grade function maps score >= 95 to A+, etc.
        # Just verify the grade assignment logic works
        assert result_f.success_level in ("poor", "below_average")
        assert result_high.success_level in ("excellent", "good")

    def test_benchmarks(self):
        result = self.ps.score(engagement_rate=6, ctr=6)
        assert result.benchmarks["engagement"] == "excellent"
        assert result.benchmarks["ctr"] == "excellent"

    def test_scoring_count(self):
        self.ps.score()
        assert self.ps.scoring_count == 1

    def test_performance_result_to_dict(self):
        result = self.ps.score(engagement_rate=5, reach=1000, ctr=3, growth_rate=50)
        d = result.to_dict()
        assert "score" in d
        assert "grade" in d


# ─── AnalyticsManager Tests ──────────────────────────────────────────
class TestAnalyticsReport:
    def test_create(self):
        r = AnalyticsReport("facebook", "p1")
        assert r.report_id.startswith("arpt_")
        assert r.platform == "facebook"
        assert r.post_id == "p1"

    def test_to_dict(self):
        r = AnalyticsReport("fb", "p1")
        d = r.to_dict()
        assert d["platform"] == "fb"


class TestAnalyticsManager:
    def setup_method(self):
        self.mgr = AnalyticsManager()

    def _fetcher(self, platform, post_id):
        return {
            "likes": 50, "comments": 15, "shares": 10,
            "reach": 5000, "impressions": 8000,
            "link_clicks": 100, "revenue": 200, "cost": 100,
        }

    def test_analyze_post(self):
        report = self.mgr.analyze_post("facebook", "p1", self._fetcher)
        assert report is not None
        assert report.platform == "facebook"
        assert "engagement" in report.to_dict()
        assert "reach" in report.to_dict()
        assert "performance" in report.to_dict()

    def test_analyze_post_failure(self):
        def bad_fetcher(p, pid):
            raise RuntimeError("API down")
        from layers.layer07_publishing.modules.analytics_hook.exceptions import FetchError
        try:
            self.mgr.analyze_post("fb", "p1", bad_fetcher)
            assert False
        except FetchError:
            pass

    def test_get_reports(self):
        self.mgr.analyze_post("facebook", "p1", self._fetcher)
        self.mgr.analyze_post("linkedin", "p2", self._fetcher)
        all_reports = self.mgr.get_reports()
        assert len(all_reports) == 2
        fb_reports = self.mgr.get_reports("facebook")
        assert len(fb_reports) == 1

    def test_learning_signals(self):
        self.mgr.analyze_post("facebook", "p1", self._fetcher)
        signals = self.mgr.get_learning_signals()
        assert signals["available"] is True
        assert signals["report_count"] == 1
        assert "facebook" in signals["platforms"]

    def test_learning_signals_empty(self):
        signals = self.mgr.get_learning_signals()
        assert signals["available"] is False

    def test_events_tracked(self):
        self.mgr.analyze_post("facebook", "p1", self._fetcher)
        events = self.mgr.events
        assert len(events) == 1
        assert events[0]["event"] == "analytics_collected"

    def test_report_count(self):
        self.mgr.analyze_post("facebook", "p1", self._fetcher)
        assert self.mgr.report_count == 1

    def test_trend_tracked(self):
        self.mgr.analyze_post("facebook", "p1", self._fetcher)
        history = self.mgr.trend.get_history("p1")
        assert len(history) >= 1

    def test_memory_stored(self):
        self.mgr.analyze_post("facebook", "p1", self._fetcher)
        assert self.mgr.memory.record_count >= 1


# ─── Exceptions Tests ────────────────────────────────────────────────
class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(AnalyticsError, Exception)
        assert issubclass(FetchError, AnalyticsError)
        assert issubclass(NormalizationError, AnalyticsError)

    def test_message(self):
        err = FetchError("fetch failed")
        assert str(err) == "fetch failed"
