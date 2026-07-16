"""Tests for Layer 6 Module 10 — Quality Orchestrator."""
from layers.layer06_quality.modules.quality_orchestrator.quality_report import QualityReport, ModuleExecutionRecord
from layers.layer06_quality.modules.quality_orchestrator.pipeline_runner import PipelineRunner, MODULE_PIPELINE
from layers.layer06_quality.modules.quality_orchestrator.quality_orchestrator import QualityOrchestrator


# ── QualityReport Tests ──

class TestQualityReport:
    def test_basic_report(self):
        report = QualityReport(report_id="qr_1", content_id="c_1")
        assert report.report_id == "qr_1"
        assert report.is_publishable() is False

    def test_is_publishable_approve(self):
        report = QualityReport()
        report.decision = "approve"
        assert report.is_publishable()

    def test_is_publishable_approve_with_warnings(self):
        report = QualityReport()
        report.decision = "approve_with_warnings"
        assert report.is_publishable()

    def test_not_publishable_reject(self):
        report = QualityReport()
        report.decision = "reject"
        assert not report.is_publishable()

    def test_publish_readiness_label(self):
        report = QualityReport()
        report.publish_readiness = 0.95
        assert report.get_publish_readiness_label() == "Very High"
        report.publish_readiness = 0.5
        assert report.get_publish_readiness_label() == "Moderate"

    def test_to_dict(self):
        report = QualityReport(report_id="qr_1")
        report.overall_score = 95
        report.grade = "A+"
        d = report.to_dict()
        assert "overall_score" in d
        assert "is_publishable" in d
        assert "publish_readiness_label" in d


# ── ModuleExecutionRecord Tests ──

class TestModuleExecutionRecord:
    def test_basic_record(self):
        rec = ModuleExecutionRecord("safety")
        assert rec.module_name == "safety"
        assert rec.status == "pending"

    def test_to_dict(self):
        rec = ModuleExecutionRecord("seo")
        rec.status = "completed"
        rec.score = 85
        d = rec.to_dict()
        assert d["status"] == "completed"
        assert d["score"] == 85.0


# ── PipelineRunner Tests ──

class TestPipelineRunner:
    def setup_method(self):
        self.runner = PipelineRunner()

    def test_run_module_success(self):
        def mock_func(content=""):
            return {"score": 90, "confidence": 0.9, "issues_count": 0}

        record = self.runner.run_module("test_module", mock_func, {"content": "test"})
        assert record.status == "completed"
        assert record.score == 90

    def test_run_module_failure_with_retry(self):
        call_count = [0]

        def failing_func(content=""):
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary failure")
            return {"score": 85, "confidence": 0.85, "issues_count": 1}

        record = self.runner.run_module("test", failing_func, {"content": "x"}, retries=3)
        assert record.status == "completed"
        assert call_count[0] == 3

    def test_run_module_permanent_failure(self):
        def always_fail(content=""):
            raise RuntimeError("Permanent failure")

        record = self.runner.run_module("test", always_fail, {"content": "x"}, retries=1)
        assert record.status == "failed"
        assert "Permanent failure" in record.error_message

    def test_run_pipeline(self):
        module_funcs = {
            "content_quality": lambda content="", **kw: {"score": 90, "confidence": 0.9, "issues_count": 0},
            "safety": lambda content="", **kw: {"score": 95, "confidence": 0.95, "issues_count": 0},
        }
        records = self.runner.run_pipeline(module_funcs, {"content": "test"})
        assert len(records) == len(MODULE_PIPELINE)
        completed = [r for r in records if r.status == "completed"]
        skipped = [r for r in records if r.status == "skipped"]
        assert len(completed) == 2
        assert len(skipped) == len(MODULE_PIPELINE) - 2

    def test_get_slowest_modules(self):
        records = [
            ModuleExecutionRecord("a"),
            ModuleExecutionRecord("b"),
        ]
        records[0].duration_ms = 100
        records[1].duration_ms = 50
        slowest = self.runner.get_slowest_modules(records)
        assert slowest[0].module_name == "a"

    def test_get_failed_modules(self):
        records = [ModuleExecutionRecord("a"), ModuleExecutionRecord("b")]
        records[0].status = "completed"
        records[1].status = "failed"
        failed = self.runner.get_failed_modules(records)
        assert len(failed) == 1

    def test_execution_count(self):
        def ok(content=""):
            return {"score": 80, "confidence": 0.8, "issues_count": 0}

        self.runner.run_module("a", ok, {"content": "x"})
        self.runner.run_module("b", ok, {"content": "x"})
        assert self.runner.execution_count == 2


# ── QualityOrchestrator Tests ──

class TestQualityOrchestrator:
    def setup_method(self):
        self.orch = QualityOrchestrator()

    def test_run_basic(self):
        report = self.orch.run("AI technology post about innovation.")
        assert isinstance(report, QualityReport)
        assert report.overall_score > 0
        assert report.grade in ("A+", "A", "A-", "B+", "B", "B-", "C+", "C")
        assert report.decision in ("approve", "approve_with_warnings", "human_review", "revise")

    def test_run_with_custom_modules(self):
        def mock_content(content="", **kw):
            return {"score": 90, "confidence": 0.9, "issues_count": 0}
        def mock_safety(content="", **kw):
            return {"score": 95, "confidence": 0.95, "issues_count": 0}

        module_funcs = {"content_quality": mock_content, "safety": mock_safety}
        report = self.orch.run("Test content.", module_funcs=module_funcs)
        assert report.overall_score > 0

    def test_run_quick(self):
        result = self.orch.run_quick("Quick test content.")
        assert "overall_score" in result
        assert "decision" in result
        assert "is_publishable" in result

    def test_events_published(self):
        report = self.orch.run("Test.")
        assert len(report.events) >= 2
        assert report.events[0]["event"] == "quality_started"
        assert report.events[1]["event"] == "quality_completed"

    def test_history_tracked(self):
        self.orch.run("Content 1.")
        self.orch.run("Content 2.")
        history = self.orch.get_history()
        assert len(history) == 2

    def test_get_latest(self):
        self.orch.run("Content 1.")
        self.orch.run("Content 2.")
        latest = self.orch.get_latest()
        assert latest is not None

    def test_get_average_score(self):
        self.orch.run("Content 1.")
        self.orch.run("Content 2.")
        avg = self.orch.get_average_score()
        assert avg > 0

    def test_get_statistics(self):
        self.orch.run("Content 1.")
        stats = self.orch.get_statistics()
        assert stats["total_runs"] == 1
        assert "avg_score" in stats
        assert "decisions" in stats

    def test_orchestration_count(self):
        self.orch.run("Test 1")
        self.orch.run("Test 2")
        assert self.orch.orchestration_count == 2

    def test_report_metadata(self):
        report = self.orch.run("AI technology post.")
        assert "platform" in report.metadata
        assert "content_length" in report.metadata
        assert "modules_executed" in report.metadata

    def test_publish_readiness(self):
        report = self.orch.run("Quality content about AI.")
        assert 0.0 <= report.publish_readiness <= 1.0

    def test_report_to_dict(self):
        report = self.orch.run("Test content.")
        d = report.to_dict()
        assert "report_id" in d
        assert "overall_score" in d
        assert "module_records" in d
        assert "events" in d

    def test_long_content(self):
        content = "AI technology is great. " * 100
        report = self.orch.run(content)
        assert report.overall_score > 0

    def test_empty_content(self):
        report = self.orch.run("")
        assert isinstance(report, QualityReport)
