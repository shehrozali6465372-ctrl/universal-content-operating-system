"""Evidence-gate and isolation tests for the Layer 9 production engine."""
from pathlib import Path

import pytest

from layers.layer09_learning.modules.autonomous_learning.engine import AutonomousLearningEngine
from layers.layer09_learning.modules.autonomous_learning.scope import LearningScope


def test_scope_keys_are_distinct():
    a = LearningScope("youtube", "ai")
    b = LearningScope("tiktok", "ai")
    c = LearningScope("youtube", "fitness")
    assert len({a.key, b.key, c.key}) == 3


def test_training_refuses_insufficient_evidence(tmp_path: Path):
    engine = AutonomousLearningEngine(tmp_path / "learning.db")
    scope = LearningScope("youtube", "ai")
    engine.record_outcome(scope, [1.0, 2.0], 0.25, source="verified_external_event")
    result = engine.train(scope, min_samples=20)
    assert result["status"] == "insufficient_data"
    with pytest.raises(RuntimeError):
        engine.predict(scope, [1.0, 2.0])


def test_outcomes_never_cross_scope(tmp_path: Path):
    engine = AutonomousLearningEngine(tmp_path / "learning.db")
    youtube_ai = LearningScope("youtube", "ai")
    tiktok_ai = LearningScope("tiktok", "ai")
    engine.record_outcome(youtube_ai, [1.0, 2.0], 0.25, source="verified_external_event")
    engine.record_outcome(tiktok_ai, [1.0, 2.0], 0.90, source="verified_external_event")
    assert engine.count(youtube_ai) == 1
    assert engine.count(tiktok_ai) == 1
    assert engine.audit_scope_isolation([youtube_ai, tiktok_ai])["isolated"] is True
