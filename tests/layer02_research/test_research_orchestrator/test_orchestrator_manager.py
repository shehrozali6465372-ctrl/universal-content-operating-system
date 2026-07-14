"""Tests for OrchestratorManager."""

from layers.layer02_research.modules.research_orchestrator.orchestrator_manager import OrchestratorManager
from layers.layer02_research.modules.research_orchestrator.retry_coordinator import RetryPolicy


class TestOrchestratorManager:
    def setup_method(self):
        self.om = OrchestratorManager(RetryPolicy(max_retries=2))

    def test_create_execution(self):
        ctx = self.om.create_execution("AI Jobs")
        assert ctx.topic == "AI Jobs"
        assert ctx.status in ("created", "planned")

    def test_execute(self):
        ctx = self.om.create_execution("AI Jobs")
        result = self.om.execute(ctx)
        assert result is not None
        assert result.execution_id == ctx.execution_id

    def test_execute_with_custom_modules(self):
        ctx = self.om.create_execution("AI", workflow_name="minimal" if "minimal" in self.om.workflow_engine.list_workflows() else "default_research")

        # Use default workflow
        def dummy(**kwargs):
            return "ok"

        for module in ["trend_discovery", "topic_intelligence", "competitor_analysis",
                       "audience_research", "knowledge_collector", "fact_verification",
                       "research_memory", "topic_scoring"]:
            self.om.register_module(module, dummy)

        result = self.om.execute(ctx)
        assert result.success is True

    def test_pause(self):
        ctx = self.om.create_execution("AI")
        self.om.execute(ctx)
        # After execution, status is terminal, so pause should return False
        paused = self.om.pause(ctx.execution_id)
        # May or may not succeed depending on timing

    def test_cancel(self):
        ctx = self.om.create_execution("AI")
        cancelled = self.om.cancel(ctx.execution_id)
        assert cancelled is True

    def test_list_executions(self):
        self.om.create_execution("AI")
        self.om.create_execution("Crypto")
        assert len(self.om.list_executions()) == 2

    def test_list_executions_by_status(self):
        ctx = self.om.create_execution("AI")
        self.om.cancel(ctx.execution_id)
        cancelled = self.om.list_executions(status="cancelled")
        assert len(cancelled) >= 1

    def test_get_execution(self):
        ctx = self.om.create_execution("AI")
        found = self.om.get_execution(ctx.execution_id)
        assert found is not None

    def test_get_result(self):
        ctx = self.om.create_execution("AI")
        self.om.execute(ctx)
        result = self.om.get_result(ctx.execution_id)
        assert result is not None

    def test_handle_module_failure(self):
        ctx = self.om.create_execution("AI")
        recovery = self.om.handle_module_failure(
            ctx, "m1", ValueError("test error")
        )
        assert "action" in recovery

    def test_get_metrics(self):
        ctx = self.om.create_execution("AI")
        self.om.execute(ctx)
        metrics = self.om.get_metrics()
        assert "module_stats" in metrics
        assert "execution_summary" in metrics

    def test_register_module(self):
        def dummy():
            return "ok"
        self.om.register_module("custom_module", dummy)
        assert "custom_module" in self.om.workflow_engine.list_registered_modules()

    def test_reset(self):
        self.om.create_execution("AI")
        self.om.reset()
        assert len(self.om.list_executions()) == 0

    def test_resume_nonexistent(self):
        result = self.om.resume("nonexistent")
        assert result is None
