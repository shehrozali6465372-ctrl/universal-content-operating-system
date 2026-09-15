"""Account-scoped persistence facade.

Every account-local read/write requires account_id. The facade resolves only the
account's provisioned workspace, preventing accidental cross-account history use.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .account_registry import AccountRegistry


class AccountDataStore:
    def __init__(self, registry: Optional[AccountRegistry] = None) -> None:
        self.registry = registry or AccountRegistry()

    def _db(self, account_id: str, kind: str) -> sqlite3.Connection:
        if not account_id or not account_id.strip():
            raise ValueError("account_id is required")
        if kind not in {"memory", "content", "analytics", "learning"}:
            raise ValueError(f"unsupported account store: {kind}")
        spec = self.registry.get(account_id)
        if spec is None:
            raise KeyError(f"unknown account_id: {account_id}")
        path = self.registry.workspace_path(account_id) / f"{kind}.sqlite3"
        if not path.exists():
            raise RuntimeError(f"account workspace is not provisioned: {account_id}")
        return sqlite3.connect(path)

    def put(self, account_id: str, kind: str, key: str, value: Any) -> None:
        with self._db(account_id, kind) as db:
            db.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("INSERT OR REPLACE INTO kv(key,value) VALUES(?,?)", (key, json.dumps(value, sort_keys=True)))

    def get(self, account_id: str, kind: str, key: str, default: Any = None) -> Any:
        with self._db(account_id, kind) as db:
            db.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            row = db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def append(self, account_id: str, kind: str, collection: str, value: Any) -> None:
        key = f"collection:{collection}"
        current = self.get(account_id, kind, key, [])
        if not isinstance(current, list):
            raise TypeError(f"account collection is not a list: {collection}")
        current.append(value)
        self.put(account_id, kind, key, current)

    def snapshot(self, account_id: str, kind: str) -> Dict[str, Any]:
        with self._db(account_id, kind) as db:
            db.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            rows = db.execute("SELECT key,value FROM kv ORDER BY key").fetchall()
        return {key: json.loads(value) for key, value in rows}
