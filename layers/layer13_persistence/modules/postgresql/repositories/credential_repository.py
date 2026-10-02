"""L13 credential repository: encrypted account-scoped secrets."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from layers.layer17_security.modules.encryption_engine.encryption_engine import EncryptionEngine


class CredentialRepository:
    """Persist encrypted provider credentials; plaintext never leaves caller boundary."""

    def __init__(self, database: Any = None, encryption_key: Optional[str] = None) -> None:
        if database is None:
            from layers.layer13_persistence.modules.postgresql.manager import get_database
            database = get_database()
        self._database = database
        self._pool = getattr(database, "_pool", None)
        if self._pool is None or not getattr(database, "_postgresql_available", False):
            raise RuntimeError("CredentialRepository requires canonical PostgreSQL")
        key = str(encryption_key or "").strip()
        if not key:
            raise RuntimeError("credential encryption key is not configured")
        self._crypto = EncryptionEngine()
        self._crypto.set_key(key)

    @staticmethod
    def _uuid(value: str, field: str) -> UUID:
        try:
            return UUID(str(value))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f"{field} must be a UUID") from exc

    def upsert(
        self,
        *,
        credential_ref: str,
        account_id: str,
        payload: Dict[str, str],
        platform_account_id: Optional[str] = None,
        key_version: str = "v1",
        expires_at: Optional[datetime] = None,
    ) -> str:
        ref = str(credential_ref or "").strip()
        if not ref or not account_id.strip():
            raise ValueError("credential_ref and account_id are required")
        if not isinstance(payload, dict) or not payload:
            raise ValueError("credential payload must be a non-empty object")
        encrypted = self._crypto.encrypt(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO credentials(
                  credential_id,credential_ref,account_id,platform_account_id,
                  encrypted_payload,key_version,active,expires_at,updated_at
                )
                VALUES (%s,%s,%s,%s,%s,%s,TRUE,%s,CURRENT_TIMESTAMP)
                ON CONFLICT (credential_ref) DO UPDATE SET
                  account_id=EXCLUDED.account_id,
                  platform_account_id=EXCLUDED.platform_account_id,
                  encrypted_payload=EXCLUDED.encrypted_payload,
                  key_version=EXCLUDED.key_version,
                  active=TRUE,
                  revoked_at=NULL,
                  expires_at=EXCLUDED.expires_at,
                  updated_at=CURRENT_TIMESTAMP
                RETURNING credential_id
                """,
                (
                    uuid4(),
                    ref,
                    account_id,
                    platform_account_id,
                    encrypted,
                    key_version,
                    expires_at,
                ),
            )
            return str(cur.fetchone()[0])

    def get_for_account(self, credential_ref: str, account_id: str) -> Optional[Dict[str, str]]:
        ref = str(credential_ref or "").strip()
        account = str(account_id or "").strip()
        if not ref or not account:
            return None
        row = self._pool.query_one(
            """
            SELECT encrypted_payload,key_version,platform_account_id,expires_at
            FROM credentials
            WHERE credential_ref=%s AND account_id=%s AND active=TRUE
              AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
              AND revoked_at IS NULL
            LIMIT 1
            """,
            (ref, account),
        )
        if not row:
            return None
        try:
            raw = self._crypto.decrypt(str(row["encrypted_payload"]))
            payload = json.loads(raw)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("credential ciphertext failed integrity/decryption validation") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("credential payload is not an object")
        result = {str(k): str(v) for k, v in payload.items()}
        if row.get("platform_account_id"):
            result.setdefault("platform_account_id", str(row["platform_account_id"]))
        result.setdefault("key_version", str(row.get("key_version") or ""))
        return result

    def revoke(self, credential_ref: str, account_id: str) -> bool:
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE credentials
                   SET active=FALSE,revoked_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
                 WHERE credential_ref=%s AND account_id=%s AND active=TRUE
                """,
                (credential_ref, account_id),
            )
            return cur.rowcount == 1
