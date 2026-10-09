"""SQLite-backed encrypted credential vault for small provider-token records.

Production use requires UCOS_SQLITE_CREDENTIAL_DB to point at a persistent,
private filesystem path (for example a mounted persistent disk). The module
intentionally has no ephemeral default path in production.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from uuid import uuid4

from layers.layer17_security.modules.encryption_engine.encryption_engine import EncryptionEngine


class SQLiteCredentialRepository:
    """Persist encrypted credentials in SQLite; never store token plaintext."""

    def __init__(self, *, encryption_key: str, db_path: Optional[str] = None) -> None:
        key = str(encryption_key or "").strip()
        if not key:
            raise RuntimeError("credential encryption key is not configured")
        configured_path = str(db_path or os.environ.get("UCOS_SQLITE_CREDENTIAL_DB", "")).strip()
        if not configured_path:
            raise RuntimeError("UCOS_SQLITE_CREDENTIAL_DB must point to persistent storage")
        self.path = Path(configured_path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._crypto = EncryptionEngine()
        self._crypto.set_key(key)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.path), timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    credential_id TEXT PRIMARY KEY,
                    credential_ref TEXT NOT NULL UNIQUE,
                    account_id TEXT NOT NULL,
                    platform_account_id TEXT,
                    encrypted_payload TEXT NOT NULL,
                    key_version TEXT NOT NULL DEFAULT 'v1',
                    active INTEGER NOT NULL DEFAULT 1,
                    revoked_at TEXT,
                    expires_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_credentials_account ON credentials(account_id, credential_ref, active)")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            # Some mounted filesystems do not support chmod; encryption remains mandatory.
            pass

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _expiry(value) -> Optional[str]:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            raw = str(value).strip()
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("expires_at must be an ISO-8601 datetime") from exc
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    def upsert(self, *, credential_ref: str, account_id: str, payload: Dict[str, str],
               platform_account_id: Optional[str] = None, key_version: str = "v1",
               expires_at=None) -> str:
        ref, account = str(credential_ref or "").strip(), str(account_id or "").strip()
        if not ref or not account:
            raise ValueError("credential_ref and account_id are required")
        if not isinstance(payload, dict) or not payload:
            raise ValueError("credential payload must be a non-empty object")
        encrypted = self._crypto.encrypt(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        now = self._utc_now()
        credential_id = str(uuid4())
        expiry = self._expiry(expires_at)
        with self._connect() as db:
            db.execute("""
                INSERT INTO credentials(
                    credential_id, credential_ref, account_id, platform_account_id,
                    encrypted_payload, key_version, active, revoked_at, expires_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, NULL, ?, ?, ?)
                ON CONFLICT(credential_ref) DO UPDATE SET
                    credential_id=excluded.credential_id,
                    account_id=excluded.account_id,
                    platform_account_id=excluded.platform_account_id,
                    encrypted_payload=excluded.encrypted_payload,
                    key_version=excluded.key_version,
                    active=1, revoked_at=NULL, expires_at=excluded.expires_at,
                    updated_at=excluded.updated_at
            """, (credential_id, ref, account, platform_account_id, encrypted, key_version, expiry, now, now))
        return credential_id

    def get_for_account(self, credential_ref: str, account_id: str) -> Optional[Dict[str, str]]:
        ref, account = str(credential_ref or "").strip(), str(account_id or "").strip()
        if not ref or not account:
            return None
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            row = db.execute("""
                SELECT encrypted_payload, key_version, platform_account_id
                FROM credentials
                WHERE credential_ref=? AND account_id=? AND active=1 AND revoked_at IS NULL
                  AND (expires_at IS NULL OR expires_at > ?)
                LIMIT 1
            """, (ref, account, now)).fetchone()
        if row is None:
            return None
        try:
            payload = json.loads(self._crypto.decrypt(str(row["encrypted_payload"])))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("credential ciphertext failed integrity/decryption validation") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("credential payload is not an object")
        result = {str(k): str(v) for k, v in payload.items()}
        if row["platform_account_id"]:
            result.setdefault("platform_account_id", str(row["platform_account_id"]))
        result.setdefault("key_version", str(row["key_version"] or ""))
        return result

    def revoke(self, credential_ref: str, account_id: str) -> bool:
        with self._connect() as db:
            cur = db.execute("""
                UPDATE credentials SET active=0, revoked_at=?, updated_at=?
                WHERE credential_ref=? AND account_id=? AND active=1
            """, (self._utc_now(), self._utc_now(), str(credential_ref), str(account_id)))
            return cur.rowcount == 1
