"""Account-scoped credential reference resolution owned by L17 Security.

This module resolves only an explicitly registered credential reference.  It
never falls back to process-global provider credentials or a different account.
Raw secret values are returned only to the immediate provider authentication
boundary and are not logged.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict


class AccountCredentialResolver:
    """Resolve one explicitly registered account credential without cross-account fallback."""

    @staticmethod
    def _production() -> bool:
        return os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}

    @classmethod
    def resolve(cls, credentials_ref: str, account_id: str = "") -> Dict[str, str]:
        reference = str(credentials_ref or "").strip()
        account = str(account_id or "").strip()
        if not reference:
            return {}

        # Production is DB-only: environment/file credential fallbacks are forbidden.
        if cls._production():
            if not account:
                return {}
            try:
                from layers.layer13_persistence.modules.postgresql.repositories.credential_repository import CredentialRepository
                key = os.environ.get("UCOS_CREDENTIAL_ENCRYPTION_KEY", "").strip()
                if not key:
                    return {}
                payload = CredentialRepository(encryption_key=key).get_for_account(reference, account)
                return payload or {}
            except Exception:
                # Credential resolution is a fail-closed security boundary.
                return {}

        # Non-production compatibility for local tests/dev only.
        import json
        import re
        from pathlib import Path
        safe = re.sub(r"[^A-Za-z0-9_]+", "_", reference).upper()
        for key in (reference, f"UCOS_CREDENTIALS_{safe}"):
            raw = os.environ.get(key, "").strip()
            if raw:
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    return {str(k): str(v) for k, v in value.items()}
        path = Path(reference)
        if path.is_file():
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                return {str(k): str(v) for k, v in value.items()} if isinstance(value, dict) else {}
            except (OSError, json.JSONDecodeError):
                return {}
        return {}
