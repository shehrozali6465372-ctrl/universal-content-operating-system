"""Tests for Layer 3 Module 10 — Intelligence Orchestrator (production-grade)."""
from layers.layer03_intelligence.modules.intelligence_orchestrator.intel_orchestrator import (
    IntelligenceOrchestrator, IntelligenceResult, PipelineEvent, ModuleMetrics, HealthStatus,
)


class TestIntelligenceOrchestrator:
    def setup_method(self):
        self.orch = IntelligenceOrchestrator()

    def test_analyze_basic(self):
        result = self.orch.analyze("AI Jobs")
        assert isinstance(result, IntelligenceResult)
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

    def test_analyze_returns_strategy(self):
        result = self.orch.analyze("Crypto", trend_history=[30, 50, 70])
        assert result.strategy is not None

    def test_analyze_returns_recommendations(self):
        result = self.orch.analyze("Tech", trend_history=[40, 60, 80])
        assert isinstance(result.recommendations, list)

    def test_cache(self):
        r1 = self.orch.analyze("Cached Topic")
        r2 = self.orch.analyze("Cached Topic")
        assert r1 is r2  # cached returns same object
        assert r2.metadata.get("cached") is True  # marked as cached

    def test_analyze_batch(self):
        results = self.orch.analyze_batch([{"topic": "AI"}, {"topic": "Crypto"}])
        assert len(results) == 2

    def test_analyze_batch_with_text(self):
        topics = [
            {"topic": "AI", "text": "AI is growing fast"},
            {"topic": "Crypto", "text": "Bitcoin surges"},
        ]
        results = self.orch.analyze_batch(topics)
        assert len(results) == 2

    def test_to_dict(self):
        result = self.orch.analyze("AI")
        d = result.to_dict()
        assert "topic" in d
        assert "overall_confidence" in d
        assert "processing_time_ms" in d

    def test_processing_time(self):
        result = self.orch.analyze("AI")
        assert result.processing_time_ms > 0

    def test_events_tracked(self):
        result = self.orch.analyze("AI", text="test content")
        assert len(result.events) > 0

    def test_total_analyses(self):
        assert self.orch.total_analyses == 0
        self.orch.analyze("A")
        assert self.orch.total_analyses == 1
        self.orch.analyze("B")
        assert self.orch.total_analyses == 2

    def test_get_metrics(self):
        self.orch.analyze("AI", text="test")
        metrics = self.orch.get_metrics()
        assert len(metrics) > 0

    def test_get_health(self):
        self.orch.analyze("AI")
        health = self.orch.get_health()
        assert health.status in ("healthy", "degraded")
        assert health.last_check > 0

    def test_analyze_empty_topic(self):
        result = self.orch.analyze("")
        assert result.topic == ""

    def test_analyze_long_history(self):
        history = list(range(1, 31))
        result = self.orch.analyze("Long", trend_history=history)
        assert result.trend_prediction is not None

    def test_analyze_domain(self):
        result = self.orch.analyze("AI", domain="technology")
        assert result.metadata.get("domain") == "technology"

    def test_batch_empty(self):
        results = self.orch.analyze_batch([])
        assert len(results) == 0

    def test_confidence_computed(self):
        result = self.orch.analyze("AI", text="Testing confidence calculation")
        assert 0 <= result.overall_confidence <= 1


class TestPipelineEvent:
    def test_create(self):
        e = PipelineEvent(event_type="start", module="test")
        assert e.event_type == "start"
        assert e.module == "test"

    def test_to_dict(self):
        e = PipelineEvent(event_type="complete", module="mod1")
        d = e.to_dict()
        assert "type" in d
        assert "module" in d
        assert "duration_ms" in d


class TestModuleMetrics:
    def test_initial(self):
        m = ModuleMetrics("test_module")
        assert m.execution_count == 0
        assert m.avg_time_ms == 0
        assert m.success_rate == 0

    def test_to_dict(self):
        m = ModuleMetrics("mod")
        d = m.to_dict()
        assert "module" in d
        assert "executions" in d


class TestHealthStatus:
    def test_initial(self):
        h = HealthStatus()
        assert h.status == "healthy"
        assert len(h.issues) == 0

    def test_to_dict(self):
        h = HealthStatus()
        d = h.to_dict()
        assert "status" in d
        assert "module_health" in d


class TestIntelligenceResult:
    def test_empty_result(self):
        r = IntelligenceResult()
        assert r.topic == ""
        assert r.overall_confidence == 0

    def test_to_dict_empty(self):
        r = IntelligenceResult("test")
        d = r.to_dict()
        assert d["topic"] == "test"
        assert d["content_understanding"] is None
        assert d["trend_prediction"] is None
