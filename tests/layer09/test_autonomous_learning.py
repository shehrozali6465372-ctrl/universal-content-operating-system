"""Tests for the real Layer 9 learning primitives.

These tests use explicit fixture observations only to test the implementation;
they are not production training data and are never written to production paths.
"""
from pathlib import Path

import pytest

from layers.layer09_learning.modules.autonomous_learning import AutonomousLearningEngine
from layers.layer09_learning.modules.autonomous_learning.scope import LearningScope


def test_scope_keys_are_distinct():
    a = LearningScope("youtube", "ai")
    b = LearningScope("tiktok", "ai")
    c = LearningScope("youtube", "fitness")
    assert len({a.key, b.key, c.key}) == 3


def test_events_are_hard_isolated(tmp_path: Path):
    engine = AutonomousLearningEngine(tmp_path / "learning.db")
    youtube_ai = LearningScope("youtube", "ai")
    tiktok_ai = LearningScope("tiktok", "ai")
    engine.record_outcome(youtube_ai, [1, 2], 0.8, source="test-fixture")
    assert engine.count(youtube_ai) == 1
    assert engine.count(tiktok_ai) == 0
    assert engine.audit_scope_isolation([youtube_ai, tiktok_ai])["isolated"] is True


def test_training_refuses_insufficient_evidence(tmp_path: Path):
    engine = AutonomousLearningEngine(tmp_path / "learning.db")
    scope = LearningScope("youtube", "ai")
    engine.record_outcome(scope, [1, 2], 0.8, source="test-fixture")
    result = engine.train(scope, min_samples=20)
    assert result["status"] == "insufficient_data"
    with pytest.raises(RuntimeError):
        engine.predict(scope, [1, 2])
