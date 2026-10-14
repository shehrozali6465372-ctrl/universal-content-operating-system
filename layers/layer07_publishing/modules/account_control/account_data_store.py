"""Account-scoped storage using Neon/L13 in production and SQLite in development.

Production account memory/content/analytics/learning state must survive service
restarts. It is stored in the canonical L13 PostgreSQL agent_memory table with a
collision-resistant account namespace. SQLite remains a development/test adapter.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .account_registry import AccountRegistry

_ALLOWED_KINDS = {"memory", "content", "analytics", "learning"}


def _production() -> bool:
    return os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}


def _account_level(account_id: str) -> str:
    """Return a short non-sensitive storage namespace for one account."""
    if not account_id or not account_id.strip():
        raise ValueError("account_id is required")
    # agent_memory.level is VARCHAR(50); the hash avoids path injection and
    # prevents account identifiers from being exposed in storage namespace keys.
    return "acct_" + hashlib.sha256(account_id.strip().encode("utf-8")).hexdigest()[:40]


def _decode(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


class AccountDataStore:
    """Per-account key/value store with a Neon-backed production adapter."""

    def __init__(
        self,
        registry: Optional[AccountRegistry] = None,
        database: Any = None,
    ) -> None:
        self.registry = registry or AccountRegistry()
        self._production = _production()
        self._database = None
        self._memory = None
        if self._production:
            from layers.layer13_persistence.modules.postgresql.manager import get_database

            self._database = database or get_database()
            if not bool(getattr(self._database, "_postgresql_available", False)):
                raise RuntimeError("Neon/PostgreSQL is required for production account storage")
            self._memory = getattr(self._database, "memory", None)
            if self._memory is None:
                raise RuntimeError("L13 PostgreSQL memory repository is unavailable")
            pool = getattr(self._database, "_pool", None)
            if pool is None:
                raise RuntimeError("L13 PostgreSQL connection pool is unavailable")

    @staticmethod
    def _validate(account_id: str, kind: str, key: Optional[str] = None) -> None:
        if not account_id or not account_id.strip():
            raise ValueError("account_id is required")
        if kind not in _ALLOWED_KINDS:
            raise ValueError(f"unsupported account store: {kind}")
        if key is not None and (not key or len(key) > 255):
            raise ValueError("key must be between 1 and 255 characters")

    def _account_exists(self, account_id: str) -> None:
        if self.registry.get(account_id) is None:
            raise KeyError(f"unknown account_id: {account_id}")

    def _db(self, account_id: str, kind: str) -> sqlite3.Connection:
        """Development/test-only SQLite accessor."""
        self._validate(account_id, kind)
        self._account_exists(account_id)
        if self._production:
            raise RuntimeError("SQLite account storage is disabled in production")
        path = self.registry.workspace_path(account_id) / f"{kind}.sqlite3"
        if not path.exists():
            raise RuntimeError(f"account workspace is not provisioned: {account_id}")
        db = sqlite3.connect(path, timeout=30)
        db.execute("PRAGMA busy_timeout=30000")
        return db

    def put(self, account_id: str, kind: str, key: str, value: Any) -> None:
        self._validate(account_id, kind, key)
        self._account_exists(account_id)
        if self._production:
            self._memory.save(
                _account_level(account_id), kind, key,
                json.dumps(value, sort_keys=True, separators=(",", ":"), default=str),
                tags="account-scoped", importance=0.5,
            )
            return
        with self._db(account_id, kind) as db:
            db.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute(
                "INSERT OR REPLACE INTO kv(key,value) VALUES(?,?)",
                (key, json.dumps(value, sort_keys=True)),
            )

    def get(self, account_id: str, kind: str, key: str, default: Any = None) -> Any:
        self._validate(account_id, kind, key)
        self._account_exists(account_id)
        if self._production:
            raw = self._memory.load(_account_level(account_id), kind, key)
            return _decode(raw, default) if raw is not None else default
        with self._db(account_id, kind) as db:
            db.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            row = db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return _decode(row[0], default) if row else default

    def append(self, account_id: str, kind: str, collection: str, value: Any) -> None:
        """Atomically append one item to the specified account-local collection."""
        self._validate(account_id, kind)
        self._account_exists(account_id)
        if not collection or len(collection) > 230:
            raise ValueError("collection must be between 1 and 230 characters")
        key = f"collection:{collection}"
        if self._production:
            pool = self._database._pool
            level = _account_level(account_id)
            # JSONB concatenation is one database statement, avoiding lost updates
            # when independent workers append to the same account concurrently.
            with pool.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO agent_memory(level, category, key, value, tags, importance)
                    VALUES (%s, %s, %s, %s, 'account-scoped', 0.5)
                    ON CONFLICT (level, category, key) DO UPDATE SET
                      value = (agent_memory.value::jsonb || EXCLUDED.value::jsonb)::text,
                      tags = 'account-scoped',
                      updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        level,
                        kind,
                        key,
                        json.dumps([value], sort_keys=True, separators=(",", ":"), default=str),
                    ),
                )
            return
        with self._db(account_id, kind) as db:
            db.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
            current = _decode(row[0], []) if row else []
            if not isinstance(current, list):
                db.rollback()
                raise TypeError(f"account collection is not a list: {collection}")
            current.append(value)
            db.execute(
                "INSERT OR REPLACE INTO kv(key,value) VALUES(?,?)",
                (key, json.dumps(current, sort_keys=True)),
            )
            db.commit()

    def history_baseline(self, account_id: str, kind: str = "content") -> Any:
        """Return the persisted completeness marker for account history."""
        if kind not in _ALLOWED_KINDS:
            raise ValueError(f"unsupported account store: {kind}")
        return self.get(
            account_id, "memory", f"history_baseline:{kind}:v1", default=None
        )

    def mark_history_baseline_verified(
        self,
        account_id: str,
        *,
        source: str,
        records_checked: int,
        confirmed: bool = False,
    ) -> Dict[str, Any]:
        """Mark historical coverage verified only after an explicit import/review."""
        allowed_sources = {"legacy_sqlite_import", "platform_api_import", "operator_review"}
        if not confirmed:
            raise ValueError("confirmed=True is required to certify historical coverage")
        if source not in allowed_sources:
            raise ValueError("source must identify a verified import or operator review")
        if isinstance(records_checked, bool) or not isinstance(records_checked, int) or records_checked < 0:
            raise ValueError("records_checked must be a non-negative integer")
        marker = {
            "status": "complete",
            "source": source,
            "records_checked": records_checked,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "coverage": "UCOS-managed history; off-platform history only when imported",
        }
        self.put(account_id, "memory", "history_baseline:content:v1", marker)
        return marker

    def bootstrap_legacy_store(self, account_id: str, kind: str) -> Dict[str, Any]:
        """Import an existing account-local SQLite store into Neon without overwriting Neon rows.

        The operation is production-only. If the legacy file is absent, it deliberately
        returns an incomplete status; an empty new Neon namespace is not proof that a
        previously published account has no history.
        """
        self._validate(account_id, kind)
        self._account_exists(account_id)
        if not self._production:
            return {"status": "not_required", "records_imported": 0}

        marker = self.history_baseline(account_id, kind)
        if isinstance(marker, dict) and marker.get("status") == "complete":
            return marker

        legacy_path = self.registry.workspace_path(account_id) / f"{kind}.sqlite3"
        if not legacy_path.is_file():
            return {"status": "legacy_store_missing", "records_imported": 0}

        try:
            uri = legacy_path.resolve().as_uri() + "?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=5) as legacy:
                exists = legacy.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='kv'"
                ).fetchone()
                if not exists:
                    return {"status": "legacy_history_table_missing", "records_imported": 0}
                rows = legacy.execute("SELECT key,value FROM kv ORDER BY key").fetchall()
        except Exception:
            return {"status": "legacy_store_unreadable", "records_imported": 0}

        # A provisioned SQLite file (or an empty kv table) is not evidence that
        # history was checked. Require an explicit execution_history collection.
        history_raw = next(
            (raw for key, raw in rows if str(key) == "collection:execution_history"),
            None,
        )
        if history_raw is None:
            return {"status": "legacy_history_key_missing", "records_imported": 0}
        history_events = _decode(history_raw, None)
        if not isinstance(history_events, list):
            return {"status": "legacy_history_malformed", "records_imported": 0}

        level = _account_level(account_id)
        pool = self._database._pool
        seeded = 0
        try:
            with pool.transaction() as conn:
                cursor = conn.cursor()
                for key, raw in rows:
                    if not key or len(str(key)) > 255:
                        raise ValueError("legacy store contains an invalid key")
                    cursor.execute(
                        """
                        INSERT INTO agent_memory(level, category, key, value, tags, importance)
                        VALUES (%s, %s, %s, %s, 'account-scoped legacy-import', 0.5)
                        ON CONFLICT (level, category, key) DO NOTHING
                        """,
                        (level, kind, str(key), str(raw)),
                    )
                    seeded += max(0, int(getattr(cursor, "rowcount", 0) or 0))

                verified_marker = {
                    "status": "complete",
                    "source": "legacy_sqlite_import",
                    "records_checked": len(rows),
                    "history_records": len(history_events),
                    "records_seeded": seeded,
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                    "coverage": "UCOS-managed history; off-platform history only when imported",
                }
                cursor.execute(
                    """
                    INSERT INTO agent_memory(level, category, key, value, tags, importance)
                    VALUES (%s, 'memory', %s, %s, 'account-scoped', 0.9)
                    ON CONFLICT (level, category, key) DO UPDATE SET
                      value=EXCLUDED.value, updated_at=CURRENT_TIMESTAMP
                    """,
                    (
                        level,
                        f"history_baseline:{kind}:v1",
                        json.dumps(verified_marker, sort_keys=True, separators=(",", ":")),
                    ),
                )
            return verified_marker
        except Exception:
            return {"status": "legacy_import_failed", "records_imported": 0}

    def snapshot(self, account_id: str, kind: str) -> Dict[str, Any]:
        self._validate(account_id, kind)
        self._account_exists(account_id)
        if self._production:
            level = _account_level(account_id)
            rows = self._database._pool.query(
                "SELECT key, value FROM agent_memory WHERE level = %s AND category = %s ORDER BY key",
                (level, kind),
            )
            return {str(row["key"]): _decode(row.get("value")) for row in rows}
        with self._db(account_id, kind) as db:
            db.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            rows = db.execute("SELECT key,value FROM kv ORDER BY key").fetchall()
        return {key: _decode(value) for key, value in rows}
