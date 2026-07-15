"""Tests for Layer 3, Module 5: Recommendation Engine."""
from layers.layer03_intelligence.modules.recommendation_engine import (
    RecommendationManager, CandidateGenerator, Candidate, RankingEngine,
    ConstraintFilter, DiversityEngine, NoveltyEngine, ExplanationBuilder,
    ConfidenceCalculator, RecommendationMemory, FeedbackCollector,
)


class TestCandidateGenerator:
    def setup_method(self):
        self.gen = CandidateGenerator()
    def test_from_trends(self):
        cands = self.gen.generate_from_trends([{"topic": "AI", "score": 0.9}])
        assert len(cands) == 1
        assert cands[0].topic == "AI"
    def test_from_audience(self):
        cands = self.gen.generate_from_audience([{"topic": "Career", "demand": 0.8}])
        assert len(cands) == 1
    def test_merge(self):
        g1 = [Candidate("AI", "trend", 0.9)]
        g2 = [Candidate("AI", "audience", 0.7)]
        merged = self.gen.merge_candidates([g1, g2])
        assert len(merged) == 1
        assert merged[0].base_score == 0.9


class TestRankingEngine:
    def setup_method(self):
        self.ranker = RankingEngine()
    def test_rank(self):
        cands = [Candidate("A", "trend", 0.5), Candidate("B", "trend", 0.9)]
        for c in cands:
            c.signals = {"trend_score": c.base_score}
        ranked = self.ranker.rank(cands)
        assert ranked[0].topic == "B"
        assert ranked[0].rank == 1
    def test_empty(self):
        assert self.ranker.rank([]) == []


class TestConstraintFilter:
    def setup_method(self):
        self.f = ConstraintFilter()
    def test_filter(self):
        self.f.add_simple("min_score", lambda c: c.base_score > 0.5)
        cands = [Candidate("A", "", 0.9), Candidate("B", "", 0.3)]
        result = self.f.filter(cands)
        assert len(result.passed) == 1
        assert len(result.filtered_out) == 1


class TestDiversityEngine:
    def test_diversify(self):
        engine = DiversityEngine(max_per_cluster=1)
        cands = [Candidate("A", "trend"), Candidate("B", "trend"), Candidate("C", "audience")]
        ranked = [type("R", (), {"topic": c.topic, "source": c.source, "final_score": 0.8, "signal_scores": {}})() for c in cands]
        result = engine.diversify(ranked)
        assert len(result.selected) == 2  # one per source


class TestNoveltyEngine:
    def test_novel(self):
        engine = NoveltyEngine(history_topics=["old"])
        cands = [Candidate("new_topic", "", 0.8), Candidate("old", "", 0.5)]
        result = engine.score_novelty(cands)
        assert result.novel_count == 1


class TestExplanationBuilder:
    def test_build(self):
        builder = ExplanationBuilder()
        c = Candidate("AI", "trend", 0.9)
        c.signals = {"trend_score": 0.9, "audience_demand": 0.8}
        exp = builder.build(c)
        assert len(exp.why) > 0
        assert exp.topic == "AI"
    def test_weak_signals(self):
        builder = ExplanationBuilder()
        c = Candidate("AI", "trend", 0.3)
        c.signals = {"trend_score": 0.2, "freshness": 0.1}
        exp = builder.build(c)
        assert len(exp.why_not) > 0


class TestConfidenceCalculator:
    def test_high(self):
        calc = ConfidenceCalculator()
        r = calc.calculate({"trend": 0.9, "audience": 0.8})
        assert r.overall > 0.7
        assert r.risk_level == "low"
    def test_low(self):
        calc = ConfidenceCalculator()
        r = calc.calculate({"trend": 0.2})
        assert r.risk_level == "high"


class TestRecommendationMemory:
    def setup_method(self):
        self.mem = RecommendationMemory()
    def test_store(self):
        from layers.layer03_intelligence.modules.recommendation_engine.recommendation_memory import RecRecord
        self.mem.store(RecRecord("AI", 0.9, 0.8))
        assert self.mem.count() == 1
    def test_success_rate(self):
        from layers.layer03_intelligence.modules.recommendation_engine.recommendation_memory import RecRecord
        self.mem.store(RecRecord("A", 0.9))
        self.mem.store(RecRecord("B", 0.8))
        self.mem.record_outcome("A", "success")
        self.mem.record_outcome("B", "failure")
        assert self.mem.get_success_rate() == 0.5


class TestFeedbackCollector:
    def setup_method(self):
        self.fc = FeedbackCollector()
    def test_collect(self):
        self.fc.add("AI", "engagement", 0.9)
        assert self.fc.count() == 1
    def test_average(self):
        self.fc.add("AI", "engagement", 0.8)
        self.fc.add("AI", "engagement", 0.6)
        assert self.fc.get_average("AI", "engagement") == 0.7


class TestRecommendationManager:
    def setup_method(self):
        self.mgr = RecommendationManager()
    def test_full_recommend(self):
        result = self.mgr.recommend({
            "trends": [{"topic": "AI Jobs", "score": 0.9, "momentum": 0.8}],
            "audience_gaps": [{"topic": "AI Career", "demand": 0.8}],
            "max_results": 3,
        })
        assert len(result.recommendations) > 0
        assert result.recommendations[0]["score"] > 0
        assert result.confidence is not None
    def test_empty(self):
        result = self.mgr.recommend({})
        assert result.total_candidates == 0
    def test_health(self):
        h = self.mgr.get_health()
        assert h["status"] == "healthy"
        assert len(h["modules"]) == 9
