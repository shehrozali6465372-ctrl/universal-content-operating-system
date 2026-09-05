"""Deterministic fixtures only; never used as production learning evidence."""
from pathlib import Path
import pytest
from layers.layer09_learning.modules.autonomous_learning import PolicyRegistry, LearningScope, ScopedExperiment

def test_policy_requires_evidence_for_deployment(tmp_path:Path):
    r=PolicyRegistry(str(tmp_path/"x.db")); s=LearningScope("youtube","ai"); p=r.register(s,"policy",{"hook":"v1"})
    with pytest.raises(ValueError): r.transition(s,"policy",p.version,"canary")
    assert r.transition(s,"policy",p.version,"canary",evidence_id="exp-1").status=="canary"

def test_policy_versions_are_immutable(tmp_path:Path):
    r=PolicyRegistry(str(tmp_path/"x.db")); s=LearningScope("youtube","ai"); a=r.register(s,"policy",{"x":1}); b=r.register(s,"policy",{"x":2})
    assert (a.version,b.version)==(1,2) and a.payload_hash!=b.payload_hash and r.get_active(s) is None

def test_no_cross_scope_policy_visibility(tmp_path:Path):
    r=PolicyRegistry(str(tmp_path/"x.db")); a=LearningScope("youtube","ai"); b=LearningScope("tiktok","ai"); p=r.register(a,"policy",{"x":1})
    with pytest.raises(KeyError): r.transition(b,"policy",p.version,"canary",evidence_id="e")

def test_experiment_outcome_requires_exact_scope_assignment(tmp_path:Path):
    e=ScopedExperiment(str(tmp_path/"x.db")); a=LearningScope("youtube","ai"); b=LearningScope("tiktok","ai"); e.create(a,"exp",control_policy="a",treatment_policy="b",min_samples_per_arm=2)
    with pytest.raises(KeyError): e.assign(b,"exp","subject")
    e.assign(a,"exp","subject")
    with pytest.raises(ValueError): e.record_outcome(b,"exp","subject",True)
    e.record_outcome(a,"exp","subject",True)

def test_rollback_restores_previous_exact_scope_policy(tmp_path:Path):
    r=PolicyRegistry(str(tmp_path/"x.db")); s=LearningScope("youtube","ai")
    a=r.register(s,"policy-a",{"x":1}); r.transition(s,"policy-a",a.version,"canary",evidence_id="e1"); r.transition(s,"policy-a",a.version,"active",evidence_id="e1")
    b=r.register(s,"policy-b",{"x":2}); r.transition(s,"policy-b",b.version,"canary",evidence_id="e2"); r.transition(s,"policy-b",b.version,"active",evidence_id="e2")
    from layers.layer09_learning.modules.autonomous_learning.guardrails import DeploymentGuard
    d=DeploymentGuard(r); result=d.rollback(s,"policy-b",b.version,reason="measured regression",evidence_id="monitor-3")
    assert result.action=="rollback" and r.get_active(s).policy_id=="policy-a"

def test_1000_contexts_have_distinct_scope_keys():
    keys={LearningScope(f"platform-{p}",f"niche-{n}").key for p in range(10) for n in range(100)}
    assert len(keys)==1000
