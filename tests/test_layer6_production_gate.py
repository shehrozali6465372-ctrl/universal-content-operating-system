"""Production gate tests for Layer 06 Quality."""
from __future__ import annotations

import importlib
import pkgutil
from concurrent.futures import ThreadPoolExecutor

import pytest

import layers.layer06_quality as layer06
from layers.layer06_quality.modules.human_review_engine.review_manager import ReviewManager
from layers.layer06_quality.modules.platform_compliance_engine.compliance_engine import ComplianceEngine
from layers.layer06_quality.modules.quality_orchestrator.pipeline_runner import PipelineRunner
from layers.layer06_quality.modules.quality_orchestrator.quality_orchestrator import QualityOrchestrator
from layers.layer06_quality.modules.quality_scoring_engine.quality_engine import QualityEngine
from layers.layer06_quality.modules.quality_scoring_engine.quality_result import ModuleScore
from layers.layer06_quality.modules.fact_citation_validator.fact_validator import FactValidator


def test_all_layer6_python_modules_import() -> None:
    failures = []
    for module in pkgutil.walk_packages(
        layer06.__path__, prefix="layers.layer06_quality."
    ):
        if module.ispkg:
            continue
        try:
            importlib.import_module(module.name)
        except Exception as exc:
            failures.append(f"{module.name}: {type(exc).__name__}: {exc}")
    assert not failures, "\n".join(failures)


def test_pipeline_fails_closed_for_missing_required_module() -> None:
    runner = PipelineRunner(max_retries=0)
    records = runner.run_pipeline(
        {"content_quality": lambda **_: {"score": 80, "confidence": 0.9}},
        {"content": "x"},
    )
    required_failures = [
        r.module_name for r in records
        if r.status == "failed"
    ]
    assert "fact_validation" in required_failures
    assert "safety" in required_failures


def test_pipeline_retries_and_preserves_final_failure() -> None:
    calls = {"count": 0}

    def broken(**_: object) -> dict:
        calls["count"] += 1
        raise RuntimeError("boom")

    runner = PipelineRunner(max_retries=2, retry_delay_seconds=0)
    record = runner.run_module("test", broken, {})
    assert record.status == "failed"
    assert calls["count"] == 3
    assert "RuntimeError: boom" in record.error_message


def test_quality_engine_rejects_missing_required_modules() -> None:
    engine = QualityEngine()
    result = engine.score([
        ModuleScore("content_quality", 90, 0.9),
        ModuleScore("safety", 90, 0.9),
    ])
    assert result.decision == "reject"
    assert result.hard_stops


def test_default_orchestrator_uses_real_engines_not_simulation() -> None:
    text = (
        "A practical content quality review explains the topic clearly, "
        "uses readable structure, avoids unsupported promises, and gives "
        "the reader useful next steps for applying the information today."
    )
    report = QualityOrchestrator().run(text, platform="facebook")
    names = {record.module_name: record for record in report.module_records}
    required = {
        "content_quality",
        "fact_validation",
        "safety",
        "originality",
        "seo",
        "platform_compliance",
        "brand_voice",
    }
    assert required.issubset(names)
    assert all(names[name].status == "completed" for name in required)
    assert "simulated" not in str(report.metadata).lower()


def test_fact_validator_does_not_treat_citation_presence_as_truth() -> None:
    validator = FactValidator()
    report = validator.validate(
        "The market grew by 25% in 2024 (Reuters, 2024)."
    )
    assert report.claim_validations
    assert all(
        claim.status != "verified"
        for claim in report.claim_validations
    )


def test_fact_validator_can_verify_exact_supplied_evidence() -> None:
    validator = FactValidator()
    claim = "The market grew by 25% in 2024."
    report = validator.validate(
        f"{claim} (Reuters, 2024)",
        evidence_texts=[{"source": "Reuters", "text": claim}],
    )
    assert any(c.status == "verified" for c in report.claim_validations)


def test_compliance_check_count_is_not_double_incremented() -> None:
    engine = ComplianceEngine()
    engine.check("A useful short post for readers.", "facebook")
    assert engine.check_count == 1
    engine.check_batch("A useful short post for readers.", ["facebook", "linkedin"])
    assert engine.check_count == 3


def test_human_approval_requires_review_stage_and_unique_reviewer() -> None:
    manager = ReviewManager()
    request = manager.create_request("A valid reviewable content item.")
    ok, _ = manager.approve(request.request_id, reviewer="alice")
    assert not ok

    ok, _ = manager.submit_for_review(request.request_id, actor="author")
    assert ok

    ok, _ = manager.approve(request.request_id, reviewer="alice")
    assert ok
    ok, _ = manager.approve(request.request_id, reviewer="alice")
    assert not ok
    assert request.current_approvals == 1



def test_human_review_request_ids_are_atomic_under_concurrency() -> None:
    manager = ReviewManager()

    def create(_: int) -> int:
        return manager.create_request("Concurrent review item.").request_id

    with ThreadPoolExecutor(max_workers=16) as executor:
        request_ids = list(executor.map(create, range(100)))

    assert len(request_ids) == 100
    assert len(set(request_ids)) == 100
    assert manager.check_count == 100


def test_invalid_inputs_are_rejected() -> None:
    with pytest.raises(ValueError):
        PipelineRunner(max_retries=-1)
    with pytest.raises(ValueError):
        QualityOrchestrator().run("", platform="facebook")
