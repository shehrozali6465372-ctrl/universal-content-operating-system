"""Tests for PipelineManager."""

from layers.layer02_research.modules.research_orchestrator.pipeline_manager import PipelineManager, PipelineResult
from layers.layer02_research.modules.research_orchestrator.exceptions import PipelineError


class TestPipelineResult:
    def test_create(self):
        r = PipelineResult("exec_1", "AI")
        assert r.execution_id == "exec_1"
        assert r.success is False

    def test_to_dict(self):
        d = PipelineResult("exec_1", "AI").to_dict()
        assert d["execution_id"] == "exec_1"


class TestPipelineManager:
    def setup_method(self):
        self.pm = PipelineManager()

    def test_create_pipeline(self):
        ctx = self.pm.create_pipeline("AI Jobs")
        assert ctx.topic == "AI Jobs"
        assert ctx.status == "created"

    def test_create_pipeline_invalid_workflow(self):
        try:
            self.pm.create_pipeline("AI", workflow_name="nonexistent")
            assert False, "Should have raised"
        except PipelineError:
            pass

    def test_list_pipelines(self):
        self.pm.create_pipeline("AI")
        assert len(self.pm.list_pipelines()) == 1

    def test_get_pipeline(self):
        ctx = self.pm.create_pipeline("AI")
        p = self.pm.get_pipeline(ctx.execution_id)
        assert p is not None

    def test_execute_pipeline(self):
        ctx = self.pm.create_pipeline("AI Jobs")
        result = self.pm.execute_pipeline(ctx)
        assert result is not None
        assert result.status in ("completed", "partial", "failed")

    def test_execute_pipeline_custom_workflow(self):
        wf = self.pm.workflow_engine.create_workflow("minimal")
        wf.add_step("trend_discovery")

        def dummy(**kwargs):
            return "ok"

        self.pm.workflow_engine.register_module("trend_discovery", dummy)
        ctx = self.pm.create_pipeline("AI", workflow_name="minimal")
        result = self.pm.execute_pipeline(ctx)
        assert result.success is True

    def test_reset(self):
        self.pm.create_pipeline("AI")
        self.pm.reset()
        assert len(self.pm.list_pipelines()) == 0
