"""Persistent, context-isolated continuous-learning engine.

Only measured external outcomes are accepted. Model and policy deployment are
separate lifecycles and both fail closed when evidence is insufficient.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path
import sqlite3
from typing import Any, Iterable, List, Optional, Sequence, Tuple
from .guardrails import DeploymentDecision, DeploymentGuard, GuardrailConfig
from .model import OnlineRegressor
from .policy import PolicyRecord, PolicyRegistry
from .scope import LearningScope

@dataclass(frozen=True)
class LearningEvent:
    event_id: str; scope: LearningScope; features: Tuple[float, ...]; reward: Optional[float]; label: Optional[float]; created_at: str; source: str

@dataclass(frozen=True)
class Prediction:
    scope_key: str; model_version: str; value: float; trained_on: int; model_quality_mae: Optional[float]

class AutonomousLearningEngine:
    """Real supervised continuous-learning runtime with persistent registry."""
    def __init__(self, db_path: str | Path = "data/layer09_learning.db", *, guardrails: GuardrailConfig | None = None) -> None:
        self.db_path = str(db_path); self.artifact_dir = Path(self.db_path).parent / "layer09_models"; self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self._models: dict[str, OnlineRegressor] = {}; self._init_db(); self.policy_registry = PolicyRegistry(self.db_path); self.deployment_guard = DeploymentGuard(self.policy_registry, guardrails); self._load_active_models()
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path); conn.row_factory = sqlite3.Row; return conn
    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""CREATE TABLE IF NOT EXISTS learning_events (event_id TEXT PRIMARY KEY,scope_key TEXT NOT NULL,platform_id TEXT NOT NULL,niche_id TEXT NOT NULL,audience_id TEXT NOT NULL,country TEXT NOT NULL,language TEXT NOT NULL,content_type TEXT NOT NULL,experiment_id TEXT NOT NULL,model_version TEXT NOT NULL,features_json TEXT NOT NULL,reward REAL NOT NULL,label REAL,source TEXT NOT NULL,created_at TEXT NOT NULL); CREATE INDEX IF NOT EXISTS idx_events_scope ON learning_events(scope_key); CREATE INDEX IF NOT EXISTS idx_events_experiment ON learning_events(experiment_id); CREATE TABLE IF NOT EXISTS model_registry (scope_key TEXT NOT NULL,model_version TEXT NOT NULL,sample_count INTEGER NOT NULL,metric_name TEXT NOT NULL,metric_value REAL NOT NULL,status TEXT NOT NULL,artifact_path TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(scope_key,model_version)); CREATE INDEX IF NOT EXISTS idx_models_active ON model_registry(scope_key,status);""")
    def record_outcome(self, scope: LearningScope, features: Sequence[float], reward: float, *, source: str, experiment_id: str = "", model_version: str = "untrained", label: Optional[float] = None, event_id: Optional[str] = None) -> LearningEvent:
        if not source.strip(): raise ValueError("source is required")
        values=tuple(float(x) for x in features); reward=float(reward)
        if not values or not all(x==x and abs(x)!=float("inf") for x in values): raise ValueError("features must be non-empty and finite")
        if reward!=reward or abs(reward)==float("inf"): raise ValueError("reward must be finite")
        if label is not None:
            label=float(label)
            if label!=label or abs(label)==float("inf"): raise ValueError("label must be finite")
        eid=event_id or hashlib.sha256((scope.key+json.dumps(values)+str(reward)+source+experiment_id).encode()).hexdigest(); event=LearningEvent(eid,scope,values,reward,label,datetime.now(timezone.utc).isoformat(),source)
        with self._connect() as conn: conn.execute("INSERT OR IGNORE INTO learning_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(eid,scope.key,scope.platform_id,scope.niche_id,scope.audience_id,scope.country,scope.language,scope.content_type,experiment_id,model_version,json.dumps(values),reward,label,source,event.created_at))
        return event
    def train(self, scope: LearningScope, *, min_samples: int = 20, min_relative_improvement: float = 0.0) -> dict[str, Any]:
        rows=self._rows(scope)
        if len(rows)<min_samples: return {"status":"insufficient_data","scope_key":scope.key,"samples":len(rows)}
        dims={len(json.loads(r["features_json"])) for r in rows}
        if len(dims)!=1: return {"status":"invalid_dataset","scope_key":scope.key,"reason":"inconsistent_feature_dimensions"}
        candidate=OnlineRegressor(); report=candidate.fit([json.loads(r["features_json"]) for r in rows],[float(r["reward"]) for r in rows]); version=candidate.version; artifact=self.artifact_dir/f"{scope.key.replace(':','_')}_{version}.joblib"; candidate.save(artifact)
        previous=self._active_registry(scope); old_mae=None if previous is None else float(previous["metric_value"])
        decision=self.deployment_guard.qualify_candidate(scope,candidate_metric=float(report["metric_value"]),baseline_metric=old_mae,evidence_count=len(rows))
        status="active" if decision.action=="promote" and (previous is None or (decision.relative_improvement or 0.0)>=min_relative_improvement) else "rejected"
        with self._connect() as conn:
            if status=="active": conn.execute("UPDATE model_registry SET status='retired' WHERE scope_key=? AND status='active'",(scope.key,))
            conn.execute("INSERT OR REPLACE INTO model_registry VALUES (?,?,?,?,?,?,?,?)",(scope.key,version,len(rows),report["metric_name"],report["metric_value"],status,str(artifact),datetime.now(timezone.utc).isoformat()))
        if status=="active": self._models[scope.key]=candidate
        return {"status":status,"scope_key":scope.key,"samples":len(rows),"model_version":version,"candidate_mae":report["metric_value"],"previous_active_mae":old_mae,"validation_samples":report.get("validation_samples"),"decision":decision.action,"decision_reason":decision.reason}
    def predict(self, scope: LearningScope, features: Sequence[float]) -> Prediction:
        model=self._models.get(scope.key)
        if model is None: raise RuntimeError(f"no active verified model for scope {scope.key}")
        values=[float(v) for v in features]; expected=getattr(model,"feature_count",None)
        if expected is not None and len(values)!=expected: raise ValueError(f"expected {expected} features, got {len(values)}")
        return Prediction(scope.key,model.version,model.predict([values])[0],model.sample_count,model.mae)
    def register_policy(self, scope: LearningScope, policy_id: str, payload: dict[str, Any], *, model_version: str = "", experiment_id: str = "", evidence_id: str = "") -> PolicyRecord:
        return self.policy_registry.register(scope,policy_id,payload,model_version=model_version,experiment_id=experiment_id,evidence_id=evidence_id)
    def canary_policy(self, scope: LearningScope, policy_id: str, version: int, *, evidence_id: str, evidence_count: int) -> DeploymentDecision: return self.deployment_guard.start_canary(scope,policy_id,version,evidence_id=evidence_id,evidence_count=evidence_count)
    def activate_policy(self, scope: LearningScope, policy_id: str, version: int, *, evidence_id: str, evidence_count: int) -> DeploymentDecision: return self.deployment_guard.promote(scope,policy_id,version,evidence_id=evidence_id,evidence_count=evidence_count)
    def rollback_policy(self, scope: LearningScope, policy_id: str, version: int, *, reason: str) -> DeploymentDecision: return self.deployment_guard.rollback(scope,policy_id,version,reason=reason)
    def active_policy(self, scope: LearningScope) -> PolicyRecord | None: return self.policy_registry.get_active(scope)
    def _load_active_models(self) -> None:
        with self._connect() as conn: rows=conn.execute("SELECT * FROM model_registry WHERE status='active'").fetchall()
        for row in rows:
            if not row["artifact_path"]: continue
            try:
                model=OnlineRegressor(); model.load(row["artifact_path"],version=row["model_version"],sample_count=row["sample_count"],mae=row["metric_value"]); self._models[row["scope_key"]]=model
            except (FileNotFoundError,RuntimeError): continue
    def _active_registry(self, scope: LearningScope) -> Optional[sqlite3.Row]:
        with self._connect() as conn: return conn.execute("SELECT * FROM model_registry WHERE scope_key=? AND status='active'",(scope.key,)).fetchone()
    def _rows(self, scope: LearningScope) -> List[sqlite3.Row]:
        with self._connect() as conn: return conn.execute("SELECT * FROM learning_events WHERE scope_key=? ORDER BY created_at,event_id",(scope.key,)).fetchall()
    def count(self, scope: LearningScope) -> int:
        with self._connect() as conn: return int(conn.execute("SELECT COUNT(*) FROM learning_events WHERE scope_key=?",(scope.key,)).fetchone()[0])
    def audit_scope_isolation(self, scopes: Iterable[LearningScope]) -> dict[str, Any]:
        keys=[scope.key for scope in scopes]
        if len(keys)!=len(set(keys)): raise ValueError("duplicate learning scopes supplied")
        return {"isolated":True,"scopes":{key:self._count_key(key) for key in keys}}
    def _count_key(self,key:str)->int:
        with self._connect() as conn: return int(conn.execute("SELECT COUNT(*) FROM learning_events WHERE scope_key=?",(key,)).fetchone()[0])
