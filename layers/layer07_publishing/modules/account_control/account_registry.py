"""UCOS account registry with PostgreSQL production persistence and SQLite migration/test fallback."""
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
    tenant_id: str = ""
    workspace_id: str = ""
    brand_id: str = ""
    platform_account_id: str = ""
    external_account_id: str = ""
    tenant_name: str = ""
    workspace_name: str = ""
    brand_name: str = ""
    platform_account_name: str = ""

    def validate(self) -> None:
        if not self.account_id.strip():
            raise ValueError("account_id is required")
        if not self.platform.strip():
            raise ValueError("platform is required")
        if not self.niche.strip():
            raise ValueError("niche is required")
        if _production():
            for field_name in ("tenant_id", "workspace_id", "brand_id", "platform_account_id"):
                if not str(getattr(self, field_name) or "").strip():
                    raise ValueError(f"{field_name} is required in production")


def _production() -> bool:
    return os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}


class AccountRegistry:
    """Account identity control; L13 owns production persistence."""

    def __init__(self, db_path: Optional[str] = None, workspace_root: Optional[str] = None):
        self.db_path = Path(db_path or os.getenv("UCOS_ACCOUNT_REGISTRY_DB", "./data/accounts/registry.sqlite3"))
        self.root = Path(workspace_root or os.getenv("UCOS_ACCOUNT_WORKSPACES", "./data/accounts/workspaces"))
        self._identity_repository = None
        if _production():
            from layers.layer13_persistence.modules.postgresql.repositories.identity_repository import IdentityRepository
            self._identity_repository = IdentityRepository()
            return

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)
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
        if safe != original or len(original) > 120:
            digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:12]
            safe = f"{safe[:100]}-{digest}"
        return safe

    def workspace_path(self, account_id: str) -> Path:
        path = self.root / self._safe(account_id)
        if not _production():
            path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _from_row(row: Dict[str, Any]) -> AccountSpec:
        def decoded(value: Any, default: Any) -> Any:
            if isinstance(value, (dict, list)):
                return value
            if value is None:
                return default
            try:
                return json.loads(value)
            except (TypeError, json.JSONDecodeError):
                return default

        return AccountSpec(
            account_id=str(row["account_id"]),
            platform=str(row["platform"]),
            niche=str(row["niche"]),
            display_name=str(row.get("display_name") or ""),
            audience=str(row.get("audience") or ""),
            credentials_ref=str(row.get("credentials_ref") or ""),
            affiliate_rules=decoded(row.get("affiliate_rules"), {}),
            capabilities=decoded(row.get("capabilities"), []),
            constraints=decoded(row.get("constraints"), {}),
            enabled=bool(row.get("enabled")),
            tenant_id=str(row.get("tenant_id") or ""),
            workspace_id=str(row.get("workspace_id") or ""),
            brand_id=str(row.get("brand_id") or ""),
            platform_account_id=str(row.get("platform_account_id") or ""),
            external_account_id=str(row.get("external_account_id") or ""),
            tenant_name=str(row.get("tenant_name") or ""),
            workspace_name=str(row.get("workspace_name") or ""),
            brand_name=str(row.get("brand_name") or ""),
            platform_account_name=str(row.get("platform_account_name") or ""),
        )

    def register(self, spec: AccountSpec) -> Path:
        spec.validate()
        if self._identity_repository is not None:
            self._identity_repository.upsert(asdict(spec))
            return self.workspace_path(spec.account_id)

        now = time.time()
        workspace = self.workspace_path(spec.account_id)
        (workspace / "account.json").write_text(
            json.dumps(asdict(spec), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        for kind in ("memory", "content", "analytics", "learning"):
            with sqlite3.connect(workspace / f"{kind}.sqlite3") as db:
                db.execute("CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                db.execute("INSERT OR REPLACE INTO metadata VALUES('account_id',?)", (spec.account_id,))
                db.execute("INSERT OR REPLACE INTO metadata VALUES('store_kind',?)", (kind,))
                db.execute("INSERT OR REPLACE INTO metadata VALUES('isolation','account')")
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                """INSERT INTO accounts(
                    account_id,platform,niche,display_name,audience,credentials_ref,
                    affiliate_rules,capabilities,constraints,enabled,workspace,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(account_id) DO UPDATE SET
                    platform=excluded.platform,niche=excluded.niche,display_name=excluded.display_name,
                    audience=excluded.audience,credentials_ref=excluded.credentials_ref,
                    affiliate_rules=excluded.affiliate_rules,capabilities=excluded.capabilities,
                    constraints=excluded.constraints,enabled=excluded.enabled,
                    workspace=excluded.workspace,updated_at=excluded.updated_at""",
                (
                    spec.account_id, spec.platform.strip().lower(), spec.niche.strip(),
                    spec.display_name, spec.audience, spec.credentials_ref,
                    json.dumps(spec.affiliate_rules, sort_keys=True),
                    json.dumps(spec.capabilities, sort_keys=True),
                    json.dumps(spec.constraints, sort_keys=True),
                    int(spec.enabled), str(workspace), now, now,
                ),
            )
        return workspace

    def get(self, account_id: str) -> Optional[AccountSpec]:
        if self._identity_repository is not None:
            row = self._identity_repository.get(account_id)
            return self._from_row(row) if row else None
        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                "SELECT account_id,platform,niche,display_name,audience,credentials_ref,affiliate_rules,capabilities,constraints,enabled "
                "FROM accounts WHERE account_id=?",
                (account_id,),
            ).fetchone()
        if not row:
            return None
        value = dict(row)
        return self._from_row(value)

    def list(self, platform: Optional[str] = None, enabled_only: bool = True) -> List[AccountSpec]:
        if self._identity_repository is not None:
            return [self._from_row(row) for row in self._identity_repository.list(platform, enabled_only)]

        query = (
            "SELECT account_id,platform,niche,display_name,audience,credentials_ref,"
            "affiliate_rules,capabilities,constraints,enabled FROM accounts"
        )
        args: List[Any] = []
        clauses: List[str] = []
        if platform:
            clauses.append("platform=?")
            args.append(platform.strip().lower())
        if enabled_only:
            clauses.append("enabled=1")
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY account_id"
        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(query, args).fetchall()
        return [self._from_row(dict(row)) for row in rows]

    def disable(self, account_id: str) -> bool:
        if self._identity_repository is not None:
            return self._identity_repository.disable(account_id)
        with sqlite3.connect(self.db_path) as db:
            return db.execute(
                "UPDATE accounts SET enabled=0,updated_at=? WHERE account_id=?",
                (time.time(), account_id),
            ).rowcount == 1
