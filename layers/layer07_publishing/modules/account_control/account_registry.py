"""Dynamic UCOS account registry and per-account workspace provisioning."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")

@dataclass(frozen=True)
class AccountSpec:
    account_id: str
    platform: str
    niche: str
    display_name: str = ""
    audience: str = ""
    credentials_ref: str = ""
    affiliate_rules: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def validate(self) -> None:
        if not self.account_id.strip(): raise ValueError("account_id is required")
        if not self.platform.strip(): raise ValueError("platform is required")
        if not self.niche.strip(): raise ValueError("niche is required")

class AccountRegistry:
    """Accounts are data, not hard-coded slots; provisioning is idempotent."""
    def __init__(self, db_path: Optional[str] = None, workspace_root: Optional[str] = None):
        self.db_path = Path(db_path or os.getenv("UCOS_ACCOUNT_REGISTRY_DB", "./data/accounts/registry.sqlite3"))
        self.root = Path(workspace_root or os.getenv("UCOS_ACCOUNT_WORKSPACES", "./data/accounts/workspaces"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True); self.root.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS accounts(
                account_id TEXT PRIMARY KEY, platform TEXT NOT NULL, niche TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT '', audience TEXT NOT NULL DEFAULT '',
                credentials_ref TEXT NOT NULL DEFAULT '', affiliate_rules TEXT NOT NULL DEFAULT '{}',
                capabilities TEXT NOT NULL DEFAULT '[]', constraints TEXT NOT NULL DEFAULT '{}',
                enabled INTEGER NOT NULL DEFAULT 1, workspace TEXT NOT NULL,
                created_at REAL NOT NULL, updated_at REAL NOT NULL)""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts(platform)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_accounts_niche ON accounts(niche)")

    @staticmethod
    def _safe(value: str) -> str:
        original = value.strip()
        safe = _SAFE.sub("_", original)[:120] or "account"
        # Sanitisation must never merge two distinct account IDs into one workspace.
        if safe != original or len(original) > 120:
            digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:12]
            safe = f"{safe[:100]}-{digest}"
        return safe

    def workspace_path(self, account_id: str) -> Path: return self.root / self._safe(account_id)

    def register(self, spec: AccountSpec) -> Path:
        spec.validate(); now = time.time(); workspace = self.workspace_path(spec.account_id); workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "account.json").write_text(json.dumps(asdict(spec), indent=2, sort_keys=True), encoding="utf-8")
        for kind in ("memory", "content", "analytics", "learning"):
            with sqlite3.connect(workspace / f"{kind}.sqlite3") as db:
                db.execute("CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                db.execute("INSERT OR REPLACE INTO metadata VALUES('account_id',?)", (spec.account_id,))
                db.execute("INSERT OR REPLACE INTO metadata VALUES('store_kind',?)", (kind,))
                db.execute("INSERT OR REPLACE INTO metadata VALUES('isolation','account')")
        with sqlite3.connect(self.db_path) as db:
            db.execute("""INSERT INTO accounts(account_id,platform,niche,display_name,audience,credentials_ref,affiliate_rules,capabilities,constraints,enabled,workspace,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(account_id) DO UPDATE SET
                platform=excluded.platform,niche=excluded.niche,display_name=excluded.display_name,audience=excluded.audience,
                credentials_ref=excluded.credentials_ref,affiliate_rules=excluded.affiliate_rules,capabilities=excluded.capabilities,
                constraints=excluded.constraints,enabled=excluded.enabled,workspace=excluded.workspace,updated_at=excluded.updated_at""",
                (spec.account_id,spec.platform.strip().lower(),spec.niche.strip(),spec.display_name,spec.audience,spec.credentials_ref,
                 json.dumps(spec.affiliate_rules,sort_keys=True),json.dumps(spec.capabilities,sort_keys=True),json.dumps(spec.constraints,sort_keys=True),int(spec.enabled),str(workspace),now,now))
        return workspace

    def get(self, account_id: str) -> Optional[AccountSpec]:
        with sqlite3.connect(self.db_path) as db: row=db.execute("SELECT account_id,platform,niche,display_name,audience,credentials_ref,affiliate_rules,capabilities,constraints,enabled FROM accounts WHERE account_id=?",(account_id,)).fetchone()
        if not row: return None
        return AccountSpec(row[0],row[1],row[2],row[3],row[4],row[5],json.loads(row[6]),json.loads(row[7]),json.loads(row[8]),bool(row[9]))

    def list(self, platform: Optional[str]=None, enabled_only: bool=True) -> List[AccountSpec]:
        q="SELECT account_id,platform,niche,display_name,audience,credentials_ref,affiliate_rules,capabilities,constraints,enabled FROM accounts"; args=[]; clauses=[]
        if platform: clauses.append("platform=?"); args.append(platform.strip().lower())
        if enabled_only: clauses.append("enabled=1")
        if clauses: q += " WHERE " + " AND ".join(clauses)
        q += " ORDER BY account_id"
        with sqlite3.connect(self.db_path) as db: rows=db.execute(q,args).fetchall()
        return [AccountSpec(r[0],r[1],r[2],r[3],r[4],r[5],json.loads(r[6]),json.loads(r[7]),json.loads(r[8]),bool(r[9])) for r in rows]

    def disable(self, account_id: str) -> bool:
        with sqlite3.connect(self.db_path) as db: return db.execute("UPDATE accounts SET enabled=0,updated_at=? WHERE account_id=?",(time.time(),account_id)).rowcount==1
