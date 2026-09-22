"""Production architecture contract tests.

These tests verify architectural invariants that must hold across all 23 layers.
They deliberately test fail-closed behavior rather than inventing external data.
"""
from pathlib import Path

import pytest

from layers.layer05_image.modules.image_orchestrator.image_orchestrator import ImageOrchestrator
from layers.layer09_learning.modules.self_improvement.self_improvement_manager import SelfImprovementManager


ROOT = Path(__file__).resolve().parents[1]
LAYERS = ROOT / "layers"


def test_repository_has_exactly_23_architectural_layers():
    layer_dirs = sorted(
        p for p in LAYERS.iterdir()
        if p.is_dir() and p.name.startswith("layer") and p.name[5:7].isdigit()
    )
    assert len(layer_dirs) == 23
    assert [p.name for p in layer_dirs] == [f"layer{i:02d}_" + p.name.split("_", 1)[1]
                                            for i, p in enumerate(layer_dirs, 1)]


def test_every_architectural_layer_contains_python_implementation():
    for layer in sorted(LAYERS.glob("layer[0-9][0-9]_*/")):
        assert any(layer.rglob("*.py")), f"{layer.name} has no Python implementation"


def test_image_orchestration_fails_closed_without_real_provider():
    with pytest.raises(RuntimeError, match="real image provider"):
        ImageOrchestrator()


def test_learning_actions_require_observed_outcomes():
    manager = SelfImprovementManager()
    result = manager.run_improvement_cycle(
        feedback=[{"negative": True, "category": "content", "description": "weak CTA"}],
        issues=[{"category": "cta", "severity": "medium"}],
    )
    assert result.mistakes_found >= 1
    assert result.actions_created >= 1
    assert result.actions_completed == 0


def test_learning_action_can_complete_only_with_explicit_observed_outcome():
    manager = SelfImprovementManager()
    planned = manager.run_improvement_cycle(
        feedback=[{"negative": True, "category": "content", "description": "weak CTA"}],
        action_outcomes={},
    )
    assert planned.actions_created == 1
    assert planned.actions_completed == 0

    action_id = manager.action_manager.get_actions(status="planned")[0].action_id
    completed = manager.run_improvement_cycle(
        feedback=[],
        action_outcomes={action_id: 0.73},
    )
    assert completed.actions_created == 0
    assert completed.actions_completed == 0
    assert manager.action_manager.get_actions(status="completed") == []

    # Completion is allowed only when the observed outcome is supplied for
    # the action during the cycle that evaluates that action.
    manager2 = SelfImprovementManager()
    seed = manager2.run_improvement_cycle(
        feedback=[{"negative": True, "category": "content", "description": "weak CTA"}],
    )
    action_id = manager2.action_manager.get_actions(status="planned")[0].action_id
    result = manager2.run_improvement_cycle(
        feedback=[{"negative": True, "category": "content", "description": "weak CTA"}],
        action_outcomes={action_id: 0.73},
    )
    assert result.actions_created >= 1
    assert result.actions_completed == 1
    assert manager2.action_manager.get_actions(status="completed")[0].actual_impact == 0.73


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
