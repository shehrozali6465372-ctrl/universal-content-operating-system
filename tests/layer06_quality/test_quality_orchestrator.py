"""Production tests for the Layer 06 quality orchestrator."""
from layers.layer06_quality.modules.quality_orchestrator.quality_report import (
    QualityReport,
    ModuleExecutionRecord,
)
from layers.layer06_quality.modules.quality_orchestrator.pipeline_runner import (
    PipelineRunner,
    MODULE_PIPELINE,
)
from layers.layer06_quality.modules.quality_orchestrator.quality_orchestrator import (
    QualityOrchestrator,
)


VALID_CONTENT = (
    "A practical quality review explains the topic clearly, uses readable "
    "structure, avoids unsupported promises, and gives readers useful "
    "next steps for applying the information today."
)


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
        data = report.to_dict()
        assert "overall_score" in data
        assert "is_publishable" in data
        assert "publish_readiness_label" in data


class TestModuleExecutionRecord:
    def test_basic_record(self):
        rec = ModuleExecutionRecord("safety")
        assert rec.module_name == "safety"
        assert rec.status == "pending"

    def test_to_dict(self):
        rec = ModuleExecutionRecord("seo")
        rec.status = "completed"
        rec.score = 85
        data = rec.to_dict()
        assert data["status"] == "completed"
        assert data["score"] == 85.0


class TestPipelineRunner:
    def setup_method(self):
        self.runner = PipelineRunner()

    def test_run_module_success(self):
        def mock_func(content=""):
            return {"score": 90, "confidence": 0.9, "issues_count": 0}

        record = self.runner.run_module(
            "test_module", mock_func, {"content": "test"}
        )
        assert record.status == "completed"
        assert record.score == 90

    def test_run_module_failure_with_retry(self):
        call_count = [0]

        def failing_func(content=""):
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary failure")
            return {"score": 85, "confidence": 0.85, "issues_count": 1}

        record = self.runner.run_module(
            "test", failing_func, {"content": "x"}, retries=3
        )
        assert record.status == "completed"
        assert call_count[0] == 3

    def test_run_module_permanent_failure(self):
        def always_fail(content=""):
            raise RuntimeError("Permanent failure")

        record = self.runner.run_module(
            "test", always_fail, {"content": "x"}, retries=1
        )
        assert record.status == "failed"
        assert "Permanent failure" in record.error_message

    def test_run_pipeline_fails_closed_for_missing_required_modules(self):
        module_funcs = {
            "content_quality": lambda content="", **kw: {
                "score": 90, "confidence": 0.9, "issues_count": 0
            },
            "safety": lambda content="", **kw: {
                "score": 95, "confidence": 0.95, "issues_count": 0
            },
        }
        records = self.runner.run_pipeline(module_funcs, {"content": "test"})
        assert len(records) == len(MODULE_PIPELINE)
        by_name = {record.module_name: record for record in records}
        assert by_name["content_quality"].status == "completed"
        assert by_name["safety"].status == "completed"
        assert by_name["fact_validation"].status == "failed"
        assert by_name["originality"].status == "failed"
        assert by_name["human_review"].status == "skipped"

    def test_get_slowest_modules(self):
        records = [ModuleExecutionRecord("a"), ModuleExecutionRecord("b")]
        records[0].duration_ms = 100
        records[1].duration_ms = 50
        slowest = self.runner.get_slowest_modules(records)
        assert slowest[0].module_name == "a"

    def test_get_failed_modules(self):
        records = [ModuleExecutionRecord("a"), ModuleExecutionRecord("b")]
        records[0].status = "completed"
        records[1].status = "failed"
        assert len(self.runner.get_failed_modules(records)) == 1

    def test_execution_count(self):
        def ok(content=""):
            return {"score": 80, "confidence": 0.8, "issues_count": 0}

        self.runner.run_module("a", ok, {"content": "x"})
        self.runner.run_module("b", ok, {"content": "x"})
        assert self.runner.execution_count == 2


class TestQualityOrchestrator:
    def setup_method(self):
        self.orch = QualityOrchestrator()

    def test_run_basic(self):
        report = self.orch.run(VALID_CONTENT)
        assert isinstance(report, QualityReport)
        assert report.overall_score >= 0
        assert report.grade in (
            "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"
        )
        assert report.decision in (
            "approve", "approve_with_warnings", "human_review", "revise", "reject"
        )
        assert all(
            record.status == "completed"
            for record in report.module_records
            if record.module_name != "human_review"
        )

    def test_run_with_custom_modules_requires_complete_set(self):
        def mock_module(content="", **kw):
            return {"score": 90, "confidence": 0.9, "issues_count": 0}

        module_funcs = {
            name: mock_module
            for name in (
                "content_quality",
                "fact_validation",
                "safety",
                "originality",
                "seo",
                "platform_compliance",
                "brand_voice",
            )
        }
        report = self.orch.run(VALID_CONTENT, module_funcs=module_funcs)
        assert report.overall_score > 0
        assert report.metadata["modules_failed"] == 0

    def test_run_quick(self):
        result = self.orch.run_quick(VALID_CONTENT)
        assert "overall_score" in result
        assert "decision" in result
        assert "is_publishable" in result

    def test_events_published(self):
        report = self.orch.run(VALID_CONTENT)
        assert len(report.events) >= 2
        assert report.events[0]["event"] == "quality_started"
        assert report.events[1]["event"] == "quality_completed"

    def test_history_tracked(self):
        self.orch.run(VALID_CONTENT)
        self.orch.run(VALID_CONTENT + " More context.")
        assert len(self.orch.get_history()) == 2

    def test_get_latest(self):
        self.orch.run(VALID_CONTENT)
        latest = self.orch.get_latest()
        assert latest is not None

    def test_get_average_score(self):
        self.orch.run(VALID_CONTENT)
        self.orch.run(VALID_CONTENT + " More context.")
        assert self.orch.get_average_score() >= 0

    def test_get_statistics(self):
        self.orch.run(VALID_CONTENT)
        stats = self.orch.get_statistics()
        assert stats["total_runs"] == 1
        assert "avg_score" in stats
        assert "decisions" in stats

    def test_orchestration_count(self):
        self.orch.run(VALID_CONTENT)
        self.orch.run(VALID_CONTENT + " More context.")
        assert self.orch.orchestration_count == 2

    def test_report_metadata(self):
        report = self.orch.run(VALID_CONTENT)
        assert "platform" in report.metadata
        assert "content_length" in report.metadata
        assert "modules_executed" in report.metadata

    def test_publish_readiness(self):
        report = self.orch.run(VALID_CONTENT)
        assert 0.0 <= report.publish_readiness <= 1.0

    def test_report_to_dict(self):
        report = self.orch.run(VALID_CONTENT)
        data = report.to_dict()
        assert "report_id" in data
        assert "overall_score" in data
        assert "module_records" in data
        assert "events" in data

    def test_long_content(self):
        report = self.orch.run(VALID_CONTENT * 10)
        assert report.overall_score >= 0

    def test_empty_content_rejected(self):
        import pytest

        with pytest.raises(ValueError):
            self.orch.run("")
