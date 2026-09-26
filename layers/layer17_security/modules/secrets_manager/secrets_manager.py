"""Fail-closed in-memory secret manager for tests/development only."""
from __future__ import annotations

import hashlib
import hmac
import os
import time
import uuid
from typing import Any, Dict, List, Optional


class SecretEntry:
    __slots__ = ("secret_id", "key", "_value", "value_hash", "category",
                 "created_at", "rotated_at", "expires_at", "metadata")

    def __init__(self, key: str, value: str, category: str = "general") -> None:
        self.secret_id = uuid.uuid4().hex
        self.key = key
        self.value_hash = hashlib.sha256(value.encode()).hexdigest()
        self.category = category
        self.created_at = time.time()
        self.rotated_at = 0.0
        self.expires_at = 0.0
        self.metadata: Dict[str, Any] = {}
        self._value = value

    def to_dict(self) -> Dict[str, Any]:
        return {"secret_id": self.secret_id, "key": self.key,
                "category": self.category, "created_at": self.created_at}


class SecretsManager:
    def __init__(self) -> None:
        self._secrets: Dict[str, SecretEntry] = {}
        self._access_log: List[Dict[str, Any]] = []

    @staticmethod
    def _production() -> bool:
        return os.getenv("UCOS_ENV", "development").lower() in {"production", "prod"}

    def set_secret(self, key: str, value: str, category: str = "general") -> SecretEntry:
        if self._production():
            raise RuntimeError("in-memory secret storage is disabled in production")
        if not key or not value:
            raise ValueError("secret key and value are required")
        entry = SecretEntry(key, value, category)
        self._secrets[key] = entry
        return entry

    def get_secret(self, key: str) -> Optional[str]:
        entry = self._secrets.get(key)
        if entry is None:
            return None
        self._access_log.append({
            "key_hash": hashlib.sha256(key.encode()).hexdigest(),
            "time": time.time(),
        })
        return entry._value

    def delete_secret(self, key: str) -> bool:
        return self._secrets.pop(key, None) is not None

    def rotate_secret(self, key: str, new_value: str) -> bool:
        if not new_value:
            raise ValueError("new secret value is required")
        entry = self._secrets.get(key)
        if entry is None:
            return False
        entry._value = new_value
        entry.value_hash = hashlib.sha256(new_value.encode()).hexdigest()
        entry.rotated_at = time.time()
        return True

    def verify_secret(self, key: str, candidate: str) -> bool:
        entry = self._secrets.get(key)
        return entry is not None and hmac.compare_digest(
            entry.value_hash, hashlib.sha256(candidate.encode()).hexdigest()
        )

    def list_secrets(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        values = self._secrets.values()
        if category is not None:
            values = [e for e in values if e.category == category]
        return [e.to_dict() for e in values]

    def count(self) -> int:
        return len(self._secrets)

    def get_access_log(self) -> List[Dict[str, Any]]:
        return list(self._access_log)
