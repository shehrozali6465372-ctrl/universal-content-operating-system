"""Tests for Layer 3, Module 6: Learning Signals."""
from layers.layer03_intelligence.modules.learning_signals import (
    SignalManager, SignalCollector, SignalNormalizer,
    EngagementCalculator, FeedbackAnalyzer, PerformanceTracker,
)


class TestSignalCollector:
    def setup_method(self):
        self.c = SignalCollector()
    def test_add(self):
        self.c.add("facebook", "likes", 100)
        assert self.c.count() == 1
    def test_filter_by_type(self):
        self.c.add("fb", "likes", 10)
        self.c.add("fb", "shares", 5)
        assert len(self.c.get_by_type("likes")) == 1
    def test_clear(self):
        self.c.add("fb", "likes", 10)
        self.c.clear()
        assert self.c.count() == 0


class TestSignalNormalizer:
    def test_normalize(self):
        n = SignalNormalizer()
        r = n.normalize("likes", 50)
        assert 0 <= r.normalized_value <= 1
    def test_min_max(self):
        n = SignalNormalizer()
        n.normalize("x", 10)
        n.normalize("x", 20)
        r = n.normalize("x", 15)
        assert 0 < r.normalized_value < 1


class TestEngagementCalculator:
    def test_calculate(self):
        calc = EngagementCalculator()
        r = calc.calculate({"likes": 100, "comments": 20, "shares": 10}, reach=1000)
        assert 0 <= r.score <= 1
        assert r.grade in ("A+", "A", "B", "C", "D")
    def test_zero_reach(self):
        calc = EngagementCalculator()
        r = calc.calculate({"likes": 100}, reach=0)
        assert r.engagement_rate == 0


class TestFeedbackAnalyzer:
    def test_positive(self):
        fa = FeedbackAnalyzer()
        r = fa.analyze(["This is amazing and great!", "Love this content"])
        assert r.positive_ratio > 0
    def test_negative(self):
        fa = FeedbackAnalyzer()
        r = fa.analyze(["This is terrible and boring", "Hate this"])
        assert r.negative_ratio > 0
    def test_empty(self):
        r = FeedbackAnalyzer().analyze([])
        assert r.positive_ratio == 0


class TestPerformanceTracker:
    def setup_method(self):
        self.t = PerformanceTracker()
    def test_record(self):
        self.t.record("post1", {"likes": 100, "shares": 10})
        assert self.t.count() == 1
    def test_best(self):
        self.t.record("a", {"score": 5})
        self.t.record("b", {"score": 10})
        best = self.t.get_best_performing(1)
        assert best[0].post_id == "b"
    def test_trend(self):
        for i in range(5):
            self.t.record("p", {"score": i})
        assert self.t.get_trend() in ("improving", "stable", "declining", "insufficient_data")


class TestSignalManager:
    def setup_method(self):
        self.mgr = SignalManager()
    def test_analyze_full(self):
        result = self.mgr.analyze({
            "signals": [{"source": "fb", "type": "likes", "value": 100}],
            "metrics": {"likes": 100, "comments": 20, "shares": 10},
            "reach": 1000,
            "comments": ["Great post!", "Very helpful"],
            "post_id": "p1",
        })
        assert len(result.normalized_signals) > 0
        assert result.engagement is not None
        assert result.feedback is not None
    def test_health(self):
        h = self.mgr.get_health()
        assert h["status"] == "healthy"
        assert len(h["modules"]) == 5
