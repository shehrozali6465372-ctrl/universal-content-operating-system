"""Immutable, evidence-gated policy lifecycle for Layer 9."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib, json, sqlite3
from typing import Any
from .scope import LearningScope
_ALLOWED={"challenger":{"canary","rejected"},"canary":{"active","rolled_back"},"active":{"retired","rolled_back"},"retired":{"active"},"rejected":set(),"rolled_back":set()}
@dataclass(frozen=True)
class PolicyRecord:
    scope_key:str; policy_id:str; version:int; payload:dict[str,Any]; payload_hash:str; model_version:str; experiment_id:str; evidence_id:str; status:str; created_at:str
class PolicyRegistry:
    """Append-only policy versions; payloads are immutable and scope-bound."""
    def __init__(self,db_path:str="data/layer09_learning.db")->None:
        self.db_path=db_path
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS policies (scope_key TEXT NOT NULL,policy_id TEXT NOT NULL,version INTEGER NOT NULL,payload_json TEXT NOT NULL,payload_hash TEXT NOT NULL,model_version TEXT NOT NULL,experiment_id TEXT NOT NULL,evidence_id TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,activated_at TEXT,retired_at TEXT,rollback_reason TEXT,PRIMARY KEY(scope_key,policy_id,version))")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_policies_active ON policies(scope_key,status)")
    def _connect(self)->sqlite3.Connection:
        conn=sqlite3.connect(self.db_path); conn.row_factory=sqlite3.Row; return conn
    def register(self,scope:LearningScope,policy_id:str,payload:dict[str,Any],*,model_version:str="",experiment_id:str="",evidence_id:str="")->PolicyRecord:
        if not policy_id.strip() or not isinstance(payload,dict) or not payload: raise ValueError("policy_id and non-empty payload are required")
        canonical=json.dumps(payload,sort_keys=True,separators=(",",":")); digest=hashlib.sha256(canonical.encode()).hexdigest(); now=datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            version=int(conn.execute("SELECT COALESCE(MAX(version),0)+1 AS v FROM policies WHERE scope_key=? AND policy_id=?",(scope.key,policy_id)).fetchone()["v"])
            conn.execute("INSERT INTO policies(scope_key,policy_id,version,payload_json,payload_hash,model_version,experiment_id,evidence_id,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(scope.key,policy_id,version,canonical,digest,model_version,experiment_id,evidence_id,"challenger",now))
        return PolicyRecord(scope.key,policy_id,version,payload,digest,model_version,experiment_id,evidence_id,"challenger",now)
    def transition(self,scope:LearningScope,policy_id:str,version:int,target:str,*,evidence_id:str="",rollback_reason:str="")->PolicyRecord:
        if target not in _ALLOWED: raise ValueError(f"unknown policy status: {target}")
        with self._connect() as conn:
            row=conn.execute("SELECT * FROM policies WHERE scope_key=? AND policy_id=? AND version=?",(scope.key,policy_id,version)).fetchone()
            if row is None: raise KeyError("policy version not found in exact scope")
            if target not in _ALLOWED[str(row["status"])]: raise ValueError(f"invalid transition {row['status']} -> {target}")
            if target in {"canary","active"} and not (evidence_id.strip() or row["evidence_id"].strip()): raise ValueError("evidence_id is required before deployment")
            now=datetime.now(timezone.utc).isoformat()
            if target=="active": conn.execute("UPDATE policies SET status='retired',retired_at=? WHERE scope_key=? AND status='active'",(now,scope.key))
            conn.execute("UPDATE policies SET status=?,evidence_id=COALESCE(NULLIF(?,''),evidence_id),activated_at=CASE WHEN ?='active' THEN ? ELSE activated_at END,rollback_reason=CASE WHEN ?='rolled_back' THEN ? ELSE rollback_reason END WHERE scope_key=? AND policy_id=? AND version=?",(target,evidence_id,target,now,target,rollback_reason,scope.key,policy_id,version))
            row=conn.execute("SELECT * FROM policies WHERE scope_key=? AND policy_id=? AND version=?",(scope.key,policy_id,version)).fetchone()
        return self._record(row)
    def get_active(self,scope:LearningScope)->PolicyRecord|None:
        with self._connect() as conn: row=conn.execute("SELECT * FROM policies WHERE scope_key=? AND status='active' ORDER BY version DESC LIMIT 1",(scope.key,)).fetchone()
        return None if row is None else self._record(row)
    def get_safe_rollback(self,scope:LearningScope,*,exclude_policy_id:str|None=None,exclude_version:int|None=None)->PolicyRecord|None:
        with self._connect() as conn:
            q="SELECT * FROM policies WHERE scope_key=? AND status='retired'"; args=[scope.key]
            if exclude_policy_id is not None:
                q+=" AND NOT (policy_id=? AND version=?)"; args.extend([exclude_policy_id,exclude_version])
            elif exclude_version is not None:
                q+=" AND version<>?"; args.append(exclude_version)
            row=conn.execute(q+" ORDER BY activated_at DESC,version DESC LIMIT 1",args).fetchone()
        return None if row is None else self._record(row)
    def _record(self,row:sqlite3.Row)->PolicyRecord:
        return PolicyRecord(row["scope_key"],row["policy_id"],int(row["version"]),json.loads(row["payload_json"]),row["payload_hash"],row["model_version"],row["experiment_id"],row["evidence_id"],row["status"],row["created_at"])
