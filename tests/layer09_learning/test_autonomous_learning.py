"""Evidence-gate and isolation tests for the Layer 9 production engine."""
from pathlib import Path

import pytest

from layers.layer09_learning.modules.autonomous_learning.engine import AutonomousLearningEngine
from layers.layer09_learning.modules.autonomous_learning.experiment import ScopedExperiment
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


def test_experiment_requires_real_outcomes_and_evidence(tmp_path: Path):
    scope = LearningScope("youtube", "ai")
    exp = ScopedExperiment(str(tmp_path / "learning.db"))
    exp.create(scope, "exp-1", control_policy="policy-a", treatment_policy="policy-b", min_samples_per_arm=3)
    assert exp.assign(scope, "exp-1", "user-1") in {"control", "treatment"}
    result = exp.evaluate(scope, "exp-1")
    assert result.status == "insufficient_evidence"
    with pytest.raises(ValueError):
        exp.record_outcome(scope, "exp-1", "unknown-user", True)


def test_experiment_can_verify_a_large_signal(tmp_path: Path):
    scope = LearningScope("youtube", "ai")
    exp = ScopedExperiment(str(tmp_path / "learning.db"))
    exp.create(scope, "exp-2", control_policy="policy-a", treatment_policy="policy-b", min_samples_per_arm=20)
    for i in range(100):
        subject = f"subject-{i}"
        arm = exp.assign(scope, "exp-2", subject)
        success = (i % 20) < (4 if arm == "control" else 12)
        exp.record_outcome(scope, "exp-2", subject, success)
    result = exp.evaluate(scope, "exp-2")
    assert result.status == "verified_treatment"
    assert result.winner == "treatment"
    assert result.p_value is not None and result.p_value < 0.05
