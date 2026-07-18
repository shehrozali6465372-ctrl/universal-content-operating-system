"""Tests for Layer 10 Module 8 — Analytics Intelligence & Optimization Engine."""
from layers.layer10_monetization.modules.analytics_intelligence.analytics_profile import (
    AnalyticsProfile, AnalyticsProfileBuilder,
)
from layers.layer10_monetization.modules.analytics_intelligence.analytics_normalizer import (
    AnalyticsNormalizer,
)
from layers.layer10_monetization.modules.analytics_intelligence.analytics_collector import (
    AnalyticsCollector,
)
from layers.layer10_monetization.modules.analytics_intelligence.trend_analyzer import (
    TrendAnalyzer,
)
from layers.layer10_monetization.modules.analytics_intelligence.content_optimizer import (
    ContentOptimizer,
)
from layers.layer10_monetization.modules.analytics_intelligence.engagement_predictor import (
    EngagementPredictor,
)
from layers.layer10_monetization.modules.analytics_intelligence.timing_optimizer import (
    TimingOptimizer,
)
from layers.layer10_monetization.modules.analytics_intelligence.audience_insight import (
    AudienceInsight,
)
from layers.layer10_monetization.modules.analytics_intelligence.performance_scorer import (
    PerformanceScorer, GRADE_THRESHOLDS,
)
from layers.layer10_monetization.modules.analytics_intelligence.analytics_memory import (
    AnalyticsMemory,
)
from layers.layer10_monetization.modules.analytics_intelligence.analytics_report import (
    AnalyticsReportGenerator,
)
from layers.layer10_monetization.modules.analytics_intelligence.analytics_intelligence_manager import (
    AnalyticsIntelligenceManager,
)
from layers.layer10_monetization.modules.analytics_intelligence.exceptions import (
    AnalyticsError,
    CollectionError,
    NormalizationError,
    OptimizationError,
    PredictionError,
    StorageError,
    ReportError,
    AnalysisError,
)


# ─── AnalyticsProfile Tests ────────────────────────────────────
class TestAnalyticsProfile:
    def setup_method(self):
        self.profile = AnalyticsProfile("facebook", "post_123")

    def test_init(self):
        assert self.profile.profile_id.startswith("ap_")
        assert self.profile.platform == "facebook"
        assert self.profile.post_id == "post_123"

    def test_defaults(self):
        assert self.profile.impressions == 0
        assert self.profile.likes == 0
        assert self.profile.comments == 0
        assert self.profile.shares == 0
        assert self.profile.saves == 0

    def test_engagement_total(self):
        self.profile.likes = 10
        self.profile.comments = 5
        self.profile.shares = 3
        self.profile.saves = 2
        assert self.profile.get_engagement_total() == 20

    def test_engagement_rate_calc(self):
        self.profile.impressions = 1000
        self.profile.likes = 30
        self.profile.comments = 10
        rate = self.profile.get_engagement_rate_calc()
        assert rate == 0.04

    def test_engagement_rate_zero_impressions(self):
        assert self.profile.get_engagement_rate_calc() == 0.0

    def test_to_dict(self):
        self.profile.likes = 5
        d = self.profile.to_dict()
        assert "profile_id" in d
        assert "platform" in d
        assert "likes" in d
        assert d["platform"] == "facebook"


# ─── AnalyticsProfileBuilder Tests ─────────────────────────────
class TestAnalyticsProfileBuilder:
    def test_build(self):
        profile = (AnalyticsProfileBuilder("x", "post_1")
                   .content_type("thread")
                   .impressions(500)
                   .likes(20)
                   .comments(5)
                   .build())
        assert profile.platform == "x"
        assert profile.post_id == "post_1"
        assert profile.content_type == "thread"
        assert profile.impressions == 500
        assert profile.likes == 20

    def test_default_builder(self):
        profile = AnalyticsProfileBuilder().build()
        assert profile.platform == ""

    def test_fluent_chain(self):
        profile = (AnalyticsProfileBuilder("linkedin")
                   .impressions(1000)
                   .reach(800)
                   .clicks(50)
                   .views(200)
                   .build())
        assert profile.impressions == 1000
        assert profile.reach == 800


# ─── AnalyticsNormalizer Tests ─────────────────────────────────
class TestAnalyticsNormalizer:
    def setup_method(self):
        self.norm = AnalyticsNormalizer()

    def test_normalize_facebook(self):
        data = {"post_impressions": 100, "post_reach": 80}
        result = self.norm.normalize("facebook", data)
        assert result["impressions"] == 100
        assert result["reach"] == 80

    def test_normalize_instagram(self):
        data = {"impressions": 200, "likes": 30}
        result = self.norm.normalize("instagram", data)
        assert result["impressions"] == 200
        assert result["likes"] == 30

    def test_normalize_unknown_platform(self):
        data = {"custom_metric": 42}
        result = self.norm.normalize("bluesky", data)
        assert result["custom_metric"] == 42
        assert result["platform"] == "bluesky"

    def test_normalize_batch(self):
        items = [{"impressions": 10}, {"impressions": 20}]
        results = self.norm.normalize_batch("x", items)
        assert len(results) == 2

    def test_get_supported_platforms(self):
        platforms = self.norm.get_supported_platforms()
        assert "facebook" in platforms
        assert "linkedin" in platforms
        assert len(platforms) >= 5

    def test_get_mapping(self):
        mapping = self.norm.get_mapping("x")
        assert "impression_count" in mapping

    def test_stats(self):
        self.norm.normalize("facebook", {"a": 1})
        stats = self.norm.get_stats()
        assert stats["total_normalizations"] == 1


# ─── AnalyticsCollector Tests ──────────────────────────────────
class TestAnalyticsCollector:
    def setup_method(self):
        self.collector = AnalyticsCollector()

    def test_collect(self):
        profile = self.collector.collect("facebook", "post_1", {
            "impressions": 1000, "likes": 50, "comments": 10,
        })
        assert profile.platform == "facebook"
        assert profile.impressions == 1000
        assert profile.likes == 50

    def test_collect_no_data(self):
        profile = self.collector.collect("x", "post_2")
        assert profile.impressions == 0

    def test_collect_batch(self):
        items = [{"post_id": "p1", "likes": 10}, {"post_id": "p2", "likes": 20}]
        profiles = self.collector.collect_batch("linkedin", items)
        assert len(profiles) == 2

    def test_get_profiles_all(self):
        self.collector.collect("facebook", "p1")
        self.collector.collect("x", "p2")
        assert len(self.collector.get_profiles()) == 2

    def test_get_profiles_by_platform(self):
        self.collector.collect("facebook", "p1")
        self.collector.collect("facebook", "p2")
        self.collector.collect("x", "p3")
        fb = self.collector.get_profiles("facebook")
        assert len(fb) == 2

    def test_create_task(self):
        task = self.collector.create_task("facebook", ["p1", "p2"])
        assert task.task_id.startswith("act_")
        assert task.platform == "facebook"
        assert len(task.post_ids) == 2

    def test_pending_tasks(self):
        self.collector.create_task("facebook")
        self.collector.create_task("x")
        assert len(self.collector.get_pending_tasks()) == 2

    def test_stats(self):
        self.collector.collect("facebook", "p1")
        self.collector.collect("facebook", "p2")
        stats = self.collector.get_stats()
        assert stats["total_profiles"] == 2
        assert stats["by_platform"]["facebook"] == 2


# ─── TrendAnalyzer Tests ───────────────────────────────────────
class TestTrendAnalyzer:
    def setup_method(self):
        self.ta = TrendAnalyzer()

    def test_analyze_up(self):
        pattern = self.ta.analyze("engagement", [0.1, 0.2, 0.35], "facebook")
        assert pattern.direction == "up"
        assert pattern.strength > 0

    def test_analyze_down(self):
        self.ta.set_baseline("engagement", 0.5)
        pattern = self.ta.analyze("engagement", [0.5, 0.3], "facebook")
        assert pattern.direction == "down"

    def test_analyze_stable(self):
        self.ta.set_baseline("engagement", 0.5)
        pattern = self.ta.analyze("engagement", [0.5, 0.51], "facebook")
        assert pattern.direction == "stable"

    def test_analyze_single_value(self):
        pattern = self.ta.analyze("impressions", [100], "x")
        assert pattern.direction == "stable"
        assert pattern.strength == 0.0

    def test_detect_anomaly(self):
        self.ta.set_baseline("views", 100)
        assert self.ta.detect_anomaly("views", 500) is True
        assert self.ta.detect_anomaly("views", 110) is False

    def test_detect_anomaly_zero_baseline(self):
        self.ta.set_baseline("clicks", 0)
        assert self.ta.detect_anomaly("clicks", 100) is False

    def test_get_patterns(self):
        self.ta.analyze("m1", [1, 2], "facebook")
        self.ta.analyze("m2", [3, 1], "linkedin")
        fb = self.ta.get_patterns(platform="facebook")
        assert len(fb) == 1

    def test_get_patterns_by_direction(self):
        self.ta.analyze("m1", [1, 2])
        self.ta.analyze("m2", [2, 1])
        ups = self.ta.get_patterns(direction="up")
        assert len(ups) >= 1

    def test_stats(self):
        self.ta.analyze("m1", [1, 2])
        stats = self.ta.get_stats()
        assert stats["total_patterns"] == 1


# ─── ContentOptimizer Tests ────────────────────────────────────
class TestContentOptimizer:
    def setup_method(self):
        self.co = ContentOptimizer()

    def test_analyze_low_engagement(self):
        insights = self.co.analyze_content("facebook", "post",
                                           {"engagement_rate": 0.01, "ctr": 0.05})
        assert len(insights) >= 1
        assert insights[0].priority == 1

    def test_analyze_low_ctr(self):
        insights = self.co.analyze_content("x", "thread",
                                           {"engagement_rate": 0.05, "ctr": 0.005})
        ctr_insights = [i for i in insights if i.metric == "ctr"]
        assert len(ctr_insights) >= 1

    def test_analyze_high_engagement(self):
        insights = self.co.analyze_content("instagram", "reel",
                                           {"engagement_rate": 0.08, "reach": 5000})
        high_eng = [i for i in insights if "increase" in i.recommendation.lower()]
        assert len(high_eng) >= 1

    def test_get_top_content_types(self):
        self.co.analyze_content("facebook", "post", {"engagement_rate": 0.03})
        self.co.analyze_content("facebook", "video", {"engagement_rate": 0.08})
        top = self.co.get_top_content_types("facebook", 2)
        assert len(top) <= 2
        assert top[0]["score"] >= top[-1]["score"]

    def test_get_insights_by_priority(self):
        self.co.analyze_content("facebook", "post", {"engagement_rate": 0.01})
        high = self.co.get_insights(priority=1)
        assert len(high) >= 1

    def test_get_insights_by_platform(self):
        self.co.analyze_content("facebook", "post", {"engagement_rate": 0.01})
        self.co.analyze_content("x", "thread", {"engagement_rate": 0.01})
        fb = self.co.get_insights(platform="facebook")
        assert len(fb) >= 1
        x_insights = self.co.get_insights(platform="x")
        assert len(x_insights) >= 1

    def test_stats(self):
        self.co.analyze_content("facebook", "post", {"engagement_rate": 0.01})
        stats = self.co.get_stats()
        assert stats["total_insights"] >= 1


# ─── EngagementPredictor Tests ─────────────────────────────────
class TestEngagementPredictor:
    def setup_method(self):
        self.ep = EngagementPredictor()

    def test_predict(self):
        pred = self.ep.predict("AI Technology", "facebook")
        assert pred.prediction_id.startswith("ep_")
        assert pred.topic == "AI Technology"
        assert pred.platform == "facebook"
        assert pred.predicted_likes >= 0
        assert pred.confidence > 0

    def test_predict_different_platforms(self):
        fb = self.ep.predict("Test", "facebook")
        tk = self.ep.predict("Test", "tiktok")
        assert tk.predicted_likes >= fb.predicted_likes

    def test_predict_with_historical(self):
        pred = self.ep.predict("Trending", "linkedin", historical_engagement=0.5)
        assert pred.predicted_likes > 0

    def test_predict_batch(self):
        items = [{"topic": "A", "platform": "x"}, {"topic": "B", "platform": "facebook"}]
        preds = self.ep.predict_batch(items)
        assert len(preds) == 2

    def test_record_actual(self):
        pred = self.ep.predict("Test", "facebook")
        pred.record_actual(likes=20)
        assert pred.actual_likes == 20
        assert pred.accuracy is not None
        assert 0 <= pred.accuracy <= 1.0

    def test_set_base_rate(self):
        self.ep.set_base_rate("mastodon", 0.15)
        rates = self.ep.get_base_rates()
        assert rates["mastodon"] == 0.15

    def test_get_predictions(self):
        self.ep.predict("A", "facebook")
        self.ep.predict("B", "x")
        assert len(self.ep.get_predictions("facebook")) == 1
        assert len(self.ep.get_predictions()) == 2

    def test_get_avg_accuracy(self):
        pred = self.ep.predict("T", "facebook")
        pred.record_actual(likes=10)
        assert self.ep.get_avg_accuracy() > 0

    def test_virality_score(self):
        pred = self.ep.predict("Viral", "tiktok")
        assert pred.virality_score > 0

    def test_stats(self):
        self.ep.predict("A", "facebook")
        stats = self.ep.get_stats()
        assert stats["total_predictions"] == 1


# ─── TimingOptimizer Tests ─────────────────────────────────────
class TestTimingOptimizer:
    def setup_method(self):
        self.to = TimingOptimizer()

    def test_record_engagement(self):
        slot = self.to.record_engagement(9, 1, "facebook", 0.05)
        assert slot.hour == 9
        assert slot.day_of_week == 1
        assert slot.avg_engagement == 0.05

    def test_record_multiple_same_slot(self):
        self.to.record_engagement(9, 1, "facebook", 0.04)
        self.to.record_engagement(9, 1, "facebook", 0.06)
        slot = self.to.get_slot(9, 1, "facebook")
        assert slot.sample_count == 2
        assert slot.avg_engagement == 0.05

    def test_get_best_times(self):
        self.to.record_engagement(9, 1, "facebook", 0.03)
        self.to.record_engagement(18, 1, "facebook", 0.08)
        best = self.to.get_best_times("facebook", 2)
        assert len(best) == 2
        assert best[0].avg_engagement >= best[1].avg_engagement

    def test_get_best_times_by_day(self):
        self.to.record_engagement(9, 1, "facebook", 0.05)
        self.to.record_engagement(9, 3, "facebook", 0.08)
        monday = self.to.get_best_times("facebook", 5, day_of_week=1)
        assert all(s.day_of_week == 1 for s in monday)

    def test_get_slot(self):
        self.to.record_engagement(12, 0, "linkedin", 0.06)
        slot = self.to.get_slot(12, 0, "linkedin")
        assert slot is not None
        assert slot.avg_engagement == 0.06

    def test_get_slot_not_found(self):
        assert self.to.get_slot(25, 7) is None

    def test_get_slots_for_day(self):
        self.to.record_engagement(9, 1, "facebook", 0.04)
        self.to.record_engagement(18, 1, "facebook", 0.07)
        self.to.record_engagement(9, 2, "facebook", 0.03)
        day1 = self.to.get_slots_for_day(1, "facebook")
        assert len(day1) == 2

    def test_confidence_growth(self):
        for i in range(30):
            self.to.record_engagement(9, 1, "facebook", 0.05)
        slot = self.to.get_slot(9, 1, "facebook")
        assert slot.confidence >= 1.0

    def test_stats(self):
        self.to.record_engagement(9, 1, "facebook", 0.05)
        stats = self.to.get_stats()
        assert stats["total_slots"] == 1


# ─── AudienceInsight Tests ─────────────────────────────────────
class TestAudienceInsight:
    def setup_method(self):
        self.ai = AudienceInsight()

    def test_create_segment(self):
        seg = self.ai.create_segment("Young Professionals", "linkedin")
        assert seg.segment_id.startswith("aseg_")
        assert seg.label == "Young Professionals"
        assert seg.platform == "linkedin"

    def test_get_segment(self):
        seg = self.ai.create_segment("Segment A")
        retrieved = self.ai.get_segment(seg.segment_id)
        assert retrieved is not None
        assert retrieved.label == "Segment A"

    def test_get_segment_not_found(self):
        assert self.ai.get_segment("aseg_99999") is None

    def test_get_segments(self):
        self.ai.create_segment("A", "facebook")
        self.ai.create_segment("B", "x")
        fb = self.ai.get_segments("facebook")
        assert len(fb) == 1

    def test_update_segment(self):
        seg = self.ai.create_segment("Original")
        self.ai.update_segment(seg.segment_id, {"size": 1000, "engagement_rate": 0.05})
        assert seg.size == 1000
        assert seg.engagement_rate == 0.05

    def test_update_segment_not_found(self):
        assert self.ai.update_segment("aseg_99999", {"size": 100}) is False

    def test_record_sentiment(self):
        self.ai.record_sentiment("facebook", 0.8)
        self.ai.record_sentiment("facebook", 0.6)
        assert self.ai.get_avg_sentiment("facebook") == 0.7

    def test_get_avg_sentiment_empty(self):
        assert self.ai.get_avg_sentiment("unknown") == 0.0

    def test_add_behavior_insight(self):
        self.ai.add_behavior_insight({"platform": "x", "insight": "peak hours"})
        insights = self.ai.get_behavior_insights("x")
        assert len(insights) == 1

    def test_analyze(self):
        seg = self.ai.create_segment("A")
        seg.size = 100
        result = self.ai.analyze()
        assert result["total_segments"] == 1
        assert result["avg_segment_size"] == 100.0

    def test_stats(self):
        self.ai.create_segment("A")
        stats = self.ai.get_stats()
        assert stats["total_segments"] == 1


# ─── PerformanceScorer Tests ───────────────────────────────────
class TestPerformanceScorer:
    def setup_method(self):
        self.scorer = PerformanceScorer()

    def test_score(self):
        profile = AnalyticsProfile("facebook", "p1")
        profile.engagement_rate = 0.05
        profile.ctr = 0.02
        profile.likes = 50
        profile.comments = 10
        profile.shares = 5
        result = self.scorer.score(profile)
        assert result.score_id.startswith("ps_")
        assert 0 <= result.normalized_score <= 1.0
        assert result.grade in [g for _, g in GRADE_THRESHOLDS]

    def test_score_high(self):
        profile = AnalyticsProfile("facebook", "p1")
        profile.engagement_rate = 0.9
        profile.ctr = 0.8
        profile.likes = 900
        profile.comments = 200
        profile.shares = 100
        result = self.scorer.score(profile)
        assert result.normalized_score > 0.5

    def test_score_batch(self):
        profiles = [AnalyticsProfile("x", f"p{i}") for i in range(3)]
        results = self.scorer.score_batch(profiles)
        assert len(results) == 3

    def test_set_benchmark(self):
        self.scorer.set_benchmark("facebook", {"engagement_rate": 0.05, "ctr": 0.02})
        profile = AnalyticsProfile("facebook", "p1")
        profile.engagement_rate = 0.08
        result = self.scorer.compare_to_benchmark(profile)
        assert "above_benchmark" in result
        assert result["above_benchmark"] >= 1

    def test_compare_no_benchmark(self):
        profile = AnalyticsProfile("unknown_platform", "p1")
        result = self.scorer.compare_to_benchmark(profile)
        assert result["comparison"] == "no_benchmark"

    def test_get_avg_score(self):
        p1 = AnalyticsProfile("facebook", "p1")
        p1.engagement_rate = 0.05
        p2 = AnalyticsProfile("facebook", "p2")
        p2.engagement_rate = 0.10
        self.scorer.score(p1)
        self.scorer.score(p2)
        avg = self.scorer.get_avg_score("facebook")
        assert avg > 0

    def test_grade_distribution(self):
        for i in range(5):
            p = AnalyticsProfile("facebook", f"p{i}")
            self.scorer.score(p)
        dist = self.scorer.get_grade_distribution()
        assert isinstance(dist, dict)

    def test_custom_weights(self):
        scorer = PerformanceScorer(weights={"engagement_rate": 1.0})
        profile = AnalyticsProfile("x", "p1")
        profile.engagement_rate = 0.8
        result = scorer.score(profile)
        assert result.normalized_score > 0

    def test_stats(self):
        self.scorer.score(AnalyticsProfile("facebook", "p1"))
        stats = self.scorer.get_stats()
        assert stats["total_scored"] == 1

    def test_grade_thresholds_cover_full_range(self):
        assert GRADE_THRESHOLDS[-1][0] == 0.0
        assert GRADE_THRESHOLDS[0][0] == 0.9


# ─── AnalyticsMemory Tests ─────────────────────────────────────
class TestAnalyticsMemory:
    def setup_method(self):
        self.mem = AnalyticsMemory()

    def test_store(self):
        entry = self.mem.store("facebook", "p1", {"score": 0.8}, score=0.8)
        assert entry.entry_id.startswith("amem_")
        assert entry.platform == "facebook"
        assert entry.score == 0.8

    def test_store_with_tags(self):
        entry = self.mem.store("x", "p1", {}, tags=["viral", "trending"])
        assert "viral" in entry.tags

    def test_search_by_platform(self):
        self.mem.store("facebook", "p1", {"score": 0.5})
        self.mem.store("x", "p2", {"score": 0.6})
        fb = self.mem.search(platform="facebook")
        assert len(fb) == 1

    def test_search_by_content_type(self):
        self.mem.store("facebook", "p1", {}, content_type="post")
        self.mem.store("facebook", "p2", {}, content_type="reel")
        posts = self.mem.search(content_type="post")
        assert len(posts) == 1

    def test_search_by_tag(self):
        self.mem.store("x", "p1", {}, tags=["viral"])
        self.mem.store("x", "p2", {}, tags=["trending"])
        viral = self.mem.search(tag="viral")
        assert len(viral) == 1

    def test_search_by_min_score(self):
        self.mem.store("fb", "p1", {}, score=0.9)
        self.mem.store("fb", "p2", {}, score=0.3)
        high = self.mem.search(min_score=0.5)
        assert len(high) == 1

    def test_search_limit(self):
        for i in range(20):
            self.mem.store("x", f"p{i}", {})
        results = self.mem.search(limit=5)
        assert len(results) == 5

    def test_get_recent(self):
        for i in range(5):
            self.mem.store("facebook", f"p{i}", {})
        recent = self.mem.get_recent(3, "facebook")
        assert len(recent) == 3

    def test_get_best_performing(self):
        self.mem.store("fb", "p1", {}, score=0.3)
        self.mem.store("fb", "p2", {}, score=0.9)
        best = self.mem.get_best_performing("fb", 1)
        assert best[0].score == 0.9

    def test_compare_periods(self):
        import time
        now = time.time()
        self.mem.store("fb", "p1", {}, score=0.5)
        self.mem._entries[-1].created_at = now - 100
        self.mem.store("fb", "p2", {}, score=0.8)
        self.mem._entries[-1].created_at = now
        result = self.mem.compare_periods(now - 200, now - 50, now - 50, now + 50)
        assert result["period1_count"] == 1
        assert result["period2_count"] == 1

    def test_max_entries(self):
        mem = AnalyticsMemory(max_entries=3)
        for i in range(5):
            mem.store("fb", f"p{i}", {})
        assert len(mem._entries) == 3

    def test_stats(self):
        self.mem.store("facebook", "p1", {})
        self.mem.store("x", "p2", {})
        stats = self.mem.get_stats()
        assert stats["total"] == 2


# ─── AnalyticsReportGenerator Tests ────────────────────────────
class TestAnalyticsReportGenerator:
    def setup_method(self):
        self.rg = AnalyticsReportGenerator()

    def test_generate(self):
        report = self.rg.generate("daily", {"views": 1000})
        assert report.report_id.startswith("arpt_")
        assert report.data["views"] == 1000

    def test_generate_no_data(self):
        report = self.rg.generate("weekly")
        assert report.data == {}

    def test_add_insight(self):
        report = self.rg.generate("daily")
        report.add_insight("Engagement increased 15%")
        assert len(report.insights) == 1

    def test_add_recommendation(self):
        report = self.rg.generate("daily")
        report.add_recommendation("Post more at 6PM")
        assert len(report.recommendations) == 1

    def test_set_score(self):
        report = self.rg.generate("daily")
        report.set_score("engagement", 0.85)
        assert report.scores["engagement"] == 0.85

    def test_generate_performance_report(self):
        report = self.rg.generate_performance_report(
            {"engagement": 0.8, "reach": 0.6}, ["High engagement"])
        assert report.scores["engagement"] == 0.8
        assert len(report.insights) == 1

    def test_generate_optimization_report(self):
        report = self.rg.generate_optimization_report(
            ["Post more reels", "Use better hashtags"])
        assert len(report.recommendations) == 2

    def test_get_recent(self):
        for i in range(5):
            self.rg.generate(f"report_{i}")
        recent = self.rg.get_recent(3)
        assert len(recent) == 3

    def test_get_by_type(self):
        self.rg.generate("daily")
        self.rg.generate("weekly")
        self.rg.generate("daily")
        dailies = self.rg.get_by_type("daily")
        assert len(dailies) == 2

    def test_report_to_dict(self):
        report = self.rg.generate("daily")
        report.add_insight("Test")
        report.set_score("score", 0.9)
        d = report.to_dict()
        assert "insights" in d
        assert "scores" in d

    def test_report_get_summary(self):
        report = self.rg.generate("daily")
        report.add_insight("I1")
        report.add_recommendation("R1")
        summary = report.get_summary()
        assert summary["insight_count"] == 1
        assert summary["recommendation_count"] == 1

    def test_stats(self):
        self.rg.generate("daily")
        stats = self.rg.get_stats()
        assert stats["total"] == 1
        assert stats["by_type"]["daily"] == 1


# ─── AnalyticsIntelligenceManager Tests ─────────────────────────
class TestAnalyticsIntelligenceManager:
    def setup_method(self):
        self.manager = AnalyticsIntelligenceManager()

    def test_start_stop(self):
        assert self.manager.start() is True
        assert self.manager._is_running is True
        assert self.manager.stop() is True
        assert self.manager._is_running is False

    def test_collect_analytics(self):
        profile = self.manager.collect_analytics("facebook", "p1", {
            "impressions": 1000, "likes": 50, "comments": 10,
        })
        assert profile.platform == "facebook"

    def test_analyze_trends(self):
        result = self.manager.analyze_trends("facebook", "engagement", [0.1, 0.2, 0.3])
        assert "direction" in result
        assert result["direction"] == "up"

    def test_predict_engagement(self):
        result = self.manager.predict_engagement("AI Tech", "facebook")
        assert "predicted_likes" in result
        assert result["predicted_likes"] >= 0

    def test_optimize_content(self):
        result = self.manager.optimize_content("x", "thread",
                                               {"engagement_rate": 0.01, "ctr": 0.05})
        assert "insights" in result
        assert result["count"] >= 1

    def test_find_best_times(self):
        self.manager.timing_optimizer.record_engagement(9, 1, "facebook", 0.05)
        self.manager.timing_optimizer.record_engagement(18, 1, "facebook", 0.08)
        best = self.manager.find_best_times("facebook", 2)
        assert len(best) == 2

    def test_generate_report(self):
        result = self.manager.generate_report("daily", {"views": 500})
        assert "report_id" in result

    def test_health_check(self):
        health = self.manager.get_health()
        assert "collector" in health
        assert "normalizer" in health
        assert "trend_analyzer" in health
        assert "performance_scorer" in health
        assert "memory" in health
        assert "is_running" in health

    def test_run_full_pipeline(self):
        result = self.manager.run_full_pipeline("facebook", "post_1", {
            "impressions": 1000, "likes": 50, "comments": 10,
        }, topic="AI Trends")
        assert "score" in result
        assert "prediction" in result
        assert "content_insights" in result
        assert "report" in result
        assert "duration_ms" in result

    def test_run_pipeline_no_topic(self):
        result = self.manager.run_full_pipeline("x", "post_1", {
            "impressions": 500, "likes": 20,
        })
        assert "score" in result
        assert "prediction" not in result

    def test_submodule_integration(self):
        self.manager.collect_analytics("facebook", "p1", {"likes": 10})
        health = self.manager.get_health()
        assert health["collector"]["total_profiles"] == 1
        assert health["memory"]["total"] == 1


# ─── Exceptions Tests ──────────────────────────────────────────
class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(CollectionError, AnalyticsError)
        assert issubclass(NormalizationError, AnalyticsError)
        assert issubclass(OptimizationError, AnalyticsError)
        assert issubclass(PredictionError, AnalyticsError)
        assert issubclass(StorageError, AnalyticsError)
        assert issubclass(ReportError, AnalyticsError)
        assert issubclass(AnalysisError, AnalyticsError)

    def test_base_is_exception(self):
        assert issubclass(AnalyticsError, Exception)

    def test_can_be_raised(self):
        try:
            raise CollectionError("Failed to collect")
        except AnalyticsError as e:
            assert "Failed to collect" in str(e)
