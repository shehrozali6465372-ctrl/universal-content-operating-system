"""Production contracts for Layer 9.

CI must compile the exact branch revision before certification.

These tests prevent the orchestrator from silently becoming a synthetic
success generator again.
"""
from pathlib import Path

import pytest

from layers.layer09_learning.modules.learning_orchestrator.exceptions import (
    ProductionLearningDataRequired,
)
from layers.layer09_learning.modules.learning_orchestrator.learning_orchestrator import (
    LearningOrchestrator,
)


ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR = (
    ROOT
    / "layers"
    / "layer09_learning"
    / "modules"
    / "learning_orchestrator"
    / "learning_orchestrator.py"
)


def test_production_orchestrator_requires_observed_learning_signals():
    with pytest.raises(ProductionLearningDataRequired):
        LearningOrchestrator().orchestrate("content", platform="facebook")


def test_orchestrator_contains_no_synthetic_stage_success_literals():
    source = ORCHESTRATOR.read_text(encoding="utf-8")
    forbidden = (
        '"feedback_collected": True',
        '"prompts_optimized": True',
        '"strategy_optimized": True',
        '"brand_voice_learned": True',
        '"memory_evolved": True',
        '"self_improved": True',
        '"quality_calibrated": True',
        '"content_optimized": True',
        '"engagement_predicted": True',
        '"predicted_likes": 150',
    )
    for literal in forbidden:
        assert literal not in source

# Certification revision: repository-wide compile and regression gates are required.
