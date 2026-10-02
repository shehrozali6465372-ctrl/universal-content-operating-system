"""Production architecture contract tests.

These tests verify architectural invariants that must hold across all 23 layers.
They deliberately test fail-closed behavior rather than inventing external data.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ROOT / "layers"


def test_repository_has_exactly_23_architectural_layers():
    actual = {
        p.name for p in LAYERS.iterdir()
        if p.is_dir() and p.name.startswith("layer") and len(p.name) >= 7
        and p.name[5:7].isdigit()
    }
    expected = {
        "layer01_core", "layer02_research", "layer03_intelligence",
        "layer04_writing", "layer05_image", "layer06_quality",
        "layer07_publishing", "layer08_analytics", "layer09_learning",
        "layer10_monetization", "layer11_async_runtime", "layer12_ai_foundation",
        "layer13_persistence", "layer14_enterprise_integration",
        "layer15_async_runtime", "layer16_database_engineering",
        "layer17_security", "layer18_monitoring", "layer19_analytics_engine",
        "layer20_image_pipeline", "layer21_deployment",
        "layer22_documentation", "layer23_website_manager",
    }
    assert actual == expected


def test_every_architectural_layer_contains_python_implementation():
    for layer in sorted(LAYERS.glob("layer[0-9][0-9]_*/")):
        assert any(layer.rglob("*.py")), f"{layer.name} has no Python implementation"


def test_image_orchestration_fails_closed_without_real_provider():
    source = (
        ROOT / "layers" / "layer05_image" / "modules" / "image_orchestrator"
        / "image_orchestrator.py"
    ).read_text(encoding="utf-8")
    assert "if self.provider is None:" in source
    assert "A real image provider must be explicitly configured" in source
    assert "Mock image providers are forbidden in production" in source


def test_learning_actions_require_observed_outcomes():
    source = (
        ROOT / "layers" / "layer09_learning" / "modules" / "self_improvement"
        / "self_improvement_manager.py"
    ).read_text(encoding="utf-8")
    assert "outcomes = action_outcomes or {}" in source
    assert "if action.action_id in outcomes:" in source
    assert "self.action_manager.complete_action(action.action_id, actual_impact)" in source


def test_learning_action_completion_uses_explicit_observed_outcome(monkeypatch):
    source = (
        ROOT / "layers" / "layer09_learning" / "modules" / "self_improvement"
        / "self_improvement_manager.py"
    ).read_text(encoding="utf-8")
    assert "action.complete(actual_impact)" in source
    assert "else:\n                self.metrics.record_action(completed=False)" in source


def test_ci_declares_postgres_service():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "postgres:" in ci
    assert "postgres:16" in ci
    assert "POSTGRES_HOST: localhost" in ci


def test_production_code_does_not_default_to_mock_image_provider():
    source = (ROOT / "layers" / "layer05_image" / "modules" / "image_orchestrator"
              / "image_orchestrator.py").read_text(encoding="utf-8")
    assert "MockImageProvider" not in source
    assert "A real image provider must be explicitly configured" in source
