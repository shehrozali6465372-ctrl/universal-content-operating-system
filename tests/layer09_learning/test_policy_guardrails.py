"""Deterministic tests use fixtures only; they are never production evidence."""
from pathlib import Path
import pytest
from layers.layer09_learning.modules.autonomous_learning import GuardrailConfig, PolicyRegistry, LearningScope, ScopedExperiment


def test_policy_requires_evidence_for_deployment(tmp_path: Path):
    r=PolicyRegistry(str(tmp_path/"x.db")); s=LearningScope("youtube","ai")
    p=r.register(s,"policy",{"hook":"v1"})
    with pytest.raises(ValueError): r.transition(s,"policy",p.version,"canary")
    assert r.transition(s,"policy",p.version,"canary",evidence_id="exp-1").status=="canary"


def test_policy_versions_are_immutable(tmp_path: Path):
    r=PolicyRegistry(str(tmp_path/"x.db")); s=LearningScope("youtube","ai")
    a=r.register(s,"policy",{"x":1}); b=r.register(s,"policy",{"x":2})
    assert a.version==1 and b.version==2 and a.payload_hash!=b.payload_hash
    assert r.get_active(s) is None


def test_no_cross_scope_policy_visibility(tmp_path: Path):
    r=PolicyRegistry(str(tmp_path/"x.db")); a=LearningScope("youtube","ai"); b=LearningScope("tiktok","ai")
    p=r.register(a,"policy",{"x":1})
    with pytest.raises(KeyError): r.transition(b,"policy",p.version,"canary",evidence_id="e")


def test_experiment_outcome_requires_exact_scope_assignment(tmp_path: Path):
    e=ScopedExperiment(str(tmp_path/"x.db")); a=LearningScope("youtube","ai"); b=LearningScope("tiktok","ai")
    e.create(a,"exp",control_policy="a",treatment_policy="b",min_samples_per_arm=2)
    with pytest.raises(KeyError): e.assign(b,"exp","subject")
    e.assign(a,"exp","subject")
    with pytest.raises(ValueError): e.record_outcome(b,"exp","subject",True)
    e.record_outcome(a,"exp","subject",True)
