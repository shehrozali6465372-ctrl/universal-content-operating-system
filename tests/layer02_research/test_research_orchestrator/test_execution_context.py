"""Tests for ExecutionContext."""

from layers.layer02_research.modules.research_orchestrator.execution_context import ExecutionContext


class TestExecutionContext:
    def test_create(self):
        ctx = ExecutionContext("exec_1", "AI Jobs", "technology")
        assert ctx.execution_id == "exec_1"
        assert ctx.topic == "AI Jobs"
        assert ctx.niche == "technology"
        assert ctx.status == "created"

    def test_start(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.start()
        assert ctx.status == "running"
        assert ctx.started_at != ""

    def test_pause_resume(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.start()
        ctx.pause()
        assert ctx.status == "paused"
        ctx.resume()
        assert ctx.status == "resuming"

    def test_complete(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.start()
        ctx.complete(confidence=0.92)
        assert ctx.status == "completed"
        assert ctx.overall_confidence == 0.92
        assert ctx.completed_at != ""

    def test_fail(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.fail()
        assert ctx.status == "failed"

    def test_cancel(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.cancel()
        assert ctx.status == "cancelled"

    def test_complete_module(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.complete_module("trend_discovery", confidence=0.85)
        assert "trend_discovery" in ctx.completed_modules

    def test_fail_module(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.fail_module("trend_discovery")
        assert "trend_discovery" in ctx.failed_modules

    def test_complete_module_removes_from_failed(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.fail_module("trend_discovery")
        ctx.complete_module("trend_discovery", confidence=0.9)
        assert "trend_discovery" in ctx.completed_modules
        assert "trend_discovery" not in ctx.failed_modules

    def test_set_current_module(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.set_current_module("fact_verification")
        assert ctx.current_module == "fact_verification"

    def test_store_result(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.store_result("trend_discovery", {"score": 90})
        assert ctx.module_results["trend_discovery"] == {"score": 90}

    def test_get_progress_empty(self):
        ctx = ExecutionContext("exec_1", "AI")
        assert ctx.get_progress() == 0.0

    def test_get_progress(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.complete_module("m1", confidence=0.5)
        ctx.fail_module("m2")
        progress = ctx.get_progress()
        assert progress > 0.0

    def test_skip_module(self):
        ctx = ExecutionContext("exec_1", "AI")
        ctx.skip_module("m1")
        assert "m1" in ctx.skipped_modules

    def test_to_dict(self):
        ctx = ExecutionContext("exec_1", "AI", "tech")
        ctx.complete_module("trend", confidence=0.8)
        d = ctx.to_dict()
        assert d["execution_id"] == "exec_1"
        assert d["topic"] == "AI"
        assert d["progress"] > 0.0

    def test_from_dict(self):
        data = {
            "execution_id": "exec_99", "topic": "Crypto",
            "niche": "finance", "status": "completed",
            "completed_modules": ["m1", "m2"],
            "overall_confidence": 0.9,
        }
        ctx = ExecutionContext.from_dict(data)
        assert ctx.execution_id == "exec_99"
        assert ctx.topic == "Crypto"
        assert ctx.status == "completed"
        assert len(ctx.completed_modules) == 2
