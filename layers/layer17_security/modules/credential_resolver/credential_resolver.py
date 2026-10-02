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
    """Resolve one account credential reference without cross-account fallback."""

    _SAFE = re.compile(r"[^A-Za-z0-9_]+")

    @classmethod
    def _env_key(cls, reference: str) -> str:
        safe_reference = cls._SAFE.sub("_", reference).upper()\n        return f"UCOS_CREDENTIALS_{safe_reference}"

    @classmethod
    def resolve(cls, credentials_ref: str) -> Dict[str, str]:
        reference = str(credentials_ref or "").strip()
        if not reference:
            return {}

        for key in (reference, cls._env_key(reference)):
            raw = os.environ.get(key, "").strip()
            if raw:
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    return {str(k): str(v) for k, v in value.items()}

        path = Path(reference)
        if not path.is_file():
            return {}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return {str(k): str(v) for k, v in value.items()} if isinstance(value, dict) else {}
