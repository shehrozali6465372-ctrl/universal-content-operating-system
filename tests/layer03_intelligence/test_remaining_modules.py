"""Tests for Modules 5-10 (updated for production APIs)."""
from layers.layer03_intelligence.modules.recommendation_engine.recommendation_engine import RecommendationEngine, Recommendation
from layers.layer03_intelligence.modules.learning_signals.signal_collector import SignalCollector
from layers.layer03_intelligence.modules.knowledge_fusion.fusion_engine import FusionEngine
from layers.layer03_intelligence.modules.strategy_engine.strategy_engine import StrategyEngine
from layers.layer03_intelligence.modules.intelligence_memory.intel_cache import IntelligenceCache
from layers.layer03_intelligence.modules.intelligence_orchestrator.intel_orchestrator import IntelligenceOrchestrator


class TestRecommendationEngine:
    def setup_method(self): self.re = RecommendationEngine()
    def test_add_and_get(self):
        self.re.add(Recommendation("topic", "AI", "Write about AI", 0.9))
        assert self.re.count() == 1
    def test_get_top(self):
        self.re.add(Recommendation("topic", "A", "", 0.5))
        self.re.add(Recommendation("topic", "B", "", 0.9))
        top = self.re.get_top(1)
        assert top[0].title == "B"
    def test_clear(self):
        self.re.add(Recommendation("topic", "A", "", 0.5))
        self.re.clear()
        assert self.re.count() == 0


class TestSignalCollector:
    def setup_method(self): self.sc = SignalCollector()
    def test_collect(self):
        self.sc.add("facebook", "likes", 100)
        assert self.sc.count() == 1
    def test_get_by_type(self):
        self.sc.add("fb", "likes", 10)
        self.sc.add("fb", "shares", 5)
        assert len(self.sc.get_by_type("likes")) == 1
    def test_get_by_source(self):
        self.sc.add("fb", "likes", 10)
        self.sc.add("twitter", "likes", 5)
        assert len(self.sc.get_by_source("fb")) == 1
    def test_clear(self):
        self.sc.add("fb", "likes", 10)
        self.sc.clear()
        assert self.sc.count() == 0


class TestFusionEngine:
    def setup_method(self): self.fe = FusionEngine()
    def test_fuse(self):
        ui = self.fe.fuse("AI", {"trend": {"score": 0.8}, "research": {"score": 0.9}})
        assert ui.topic == "AI"
        assert ui.confidence > 0
    def test_fuse_batch(self):
        results = self.fe.fuse_batch({"A": {"r": {"score": 0.8}}, "B": {"r": {"score": 0.6}}})
        assert len(results) == 2
    def test_resolve_conflict(self):
        resolved = self.fe.resolver.resolve({"a": 0.8, "b": 0.9})
        assert "resolved" in resolved


class TestStrategyEngine:
    def setup_method(self): self.se = StrategyEngine()
    def test_short_term(self):
        plan = self.se.create_short_term("AI", 85.0, "educational")
        assert plan.horizon == "short"
        assert plan.confidence > 0
    def test_long_term(self):
        plan = self.se.create_long_term("technology", ["AI", "cloud"])
        assert plan.horizon == "long"
        assert len(plan.goals) > 0
    def test_list_plans(self):
        self.se.create_short_term("AI", 80, "info")
        self.se.create_long_term("tech", ["AI"])
        assert len(self.se.list_plans()) == 2
    def test_list_by_horizon(self):
        self.se.create_short_term("AI", 80, "info")
        self.se.create_long_term("tech", ["AI"])
        assert len(self.se.list_plans("short")) == 1


class TestIntelligenceCache:
    def setup_method(self): self.ic = IntelligenceCache(max_size=3)
    def test_store_and_get(self):
        self.ic.store("k1", {"data": 42})
        assert self.ic.get("k1") == {"data": 42}
    def test_get_miss(self):
        assert self.ic.get("missing") is None
    def test_has(self):
        self.ic.store("k1", "v1")
        assert self.ic.has("k1") is True
        assert self.ic.has("k2") is False
    def test_max_size_eviction(self):
        for i in range(5):
            self.ic.store(f"k{i}", f"v{i}")
        assert self.ic.size() == 3
    def test_hit_rate(self):
        self.ic.store("k1", "v1")
        self.ic.get("k1")
        self.ic.get("k1")
        assert self.ic.hit_rate() > 0
    def test_remove(self):
        self.ic.store("k1", "v1")
        assert self.ic.remove("k1") is True
        assert self.ic.remove("k1") is False


class TestIntelligenceOrchestrator:
    def setup_method(self): self.orch = IntelligenceOrchestrator()
    def test_analyze_basic(self):
        result = self.orch.analyze("AI Jobs")
        assert result.topic == "AI Jobs"
        assert result.overall_confidence >= 0
    def test_analyze_with_text(self):
        result = self.orch.analyze("AI", text="Artificial intelligence is transforming technology and jobs")
        assert result.content_understanding is not None
        assert result.quality is not None
        assert result.virality is not None
    def test_analyze_with_history(self):
        result = self.orch.analyze("AI", trend_history=[20, 40, 60, 80])
        assert result.trend_prediction is not None
        assert result.trend_prediction.predicted_direction == "rising"
    def test_cache(self):
        r1 = self.orch.analyze("Cached Topic")
        r2 = self.orch.analyze("Cached Topic")
        assert r1 is r2
    def test_analyze_batch(self):
        results = self.orch.analyze_batch([{"topic": "AI"}, {"topic": "Crypto"}])
        assert len(results) == 2
    def test_to_dict(self):
        result = self.orch.analyze("AI")
        d = result.to_dict()
        assert "topic" in d
        assert "overall_confidence" in d
