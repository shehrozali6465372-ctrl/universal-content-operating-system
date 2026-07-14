"""Tests for MetricsCollector."""

from layers.layer02_research.modules.research_orchestrator.metrics_collector import MetricsCollector, ModuleMetrics
from layers.layer02_research.modules.research_orchestrator.execution_context import ExecutionContext


class TestModuleMetrics:
    def test_create(self):
        m = ModuleMetrics("trend_discovery")
        assert m.module == "trend_discovery"

    def test_to_dict(self):
        m = ModuleMetrics("m1")
        m.duration_sec = 5.0
        m.confidence = 0.9
        d = m.to_dict()
        assert d["module"] == "m1"
        assert d["confidence"] == 0.9


class TestMetricsCollector:
    def setup_method(self):
        self.mc = MetricsCollector()

    def test_record_module(self):
        m = self.mc.record_module("m1", duration_sec=3.0, success=True, confidence=0.85)
        assert m.module == "m1"
        assert m.success is True

    def test_record_execution(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.complete_module("m1", confidence=0.9)
        ctx.complete_module("m2", confidence=0.85)
        metrics = self.mc.record_execution(ctx)
        assert metrics["completed"] == 2
        assert metrics["success_rate"] > 0

    def test_get_module_stats(self):
        self.mc.record_module("m1", duration_sec=2.0, confidence=0.9)
        self.mc.record_module("m1", duration_sec=4.0, confidence=0.8)
        stats = self.mc.get_module_stats("m1")
        assert stats["executions"] == 2
        assert stats["avg_duration_sec"] == 3.0
        assert stats["avg_confidence"] == 0.85

    def test_get_module_stats_empty(self):
        stats = self.mc.get_module_stats("unknown")
        assert stats["executions"] == 0

    def test_get_all_stats(self):
        self.mc.record_module("m1", duration_sec=1.0)
        self.mc.record_module("m2", duration_sec=2.0)
        all_stats = self.mc.get_all_stats()
        assert "m1" in all_stats
        assert "m2" in all_stats

    def test_get_execution_summary(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.complete()
        self.mc.record_execution(ctx)
        summary = self.mc.get_execution_summary()
        assert summary["total_executions"] == 1

    def test_get_execution_summary_empty(self):
        summary = self.mc.get_execution_summary()
        assert summary["total_executions"] == 0

    def test_get_slowest_modules(self):
        self.mc.record_module("m1", duration_sec=1.0)
        self.mc.record_module("m2", duration_sec=10.0)
        self.mc.record_module("m3", duration_sec=5.0)
        slow = self.mc.get_slowest_modules(top_n=2)
        assert slow[0]["module"] == "m2"

    def test_reset(self):
        self.mc.record_module("m1", duration_sec=1.0)
        self.mc.reset()
        assert self.mc.get_all_stats() == {}
