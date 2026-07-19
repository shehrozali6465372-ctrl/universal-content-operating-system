"""SecretsManager — secure storage and retrieval of secrets."""
from __future__ import annotations
import hashlib
import time
import uuid
from typing import Any, Dict, List, Optional


class SecretEntry:
    __slots__ = ("secret_id", "key", "_value", "value_hash", "category",
                 "created_at", "rotated_at", "expires_at", "metadata")

    def __init__(self, key: str, value: str, category: str = "general") -> None:
        self.secret_id = str(uuid.uuid4())[:12]
        self.key = key
        self.value_hash = hashlib.sha256(value.encode()).hexdigest()
        self.category = category
        self.created_at = time.time()
        self.rotated_at: float = 0.0
        self.expires_at: float = 0.0
        self.metadata: Dict[str, Any] = {}
        self._value = value

    def to_dict(self) -> Dict[str, Any]:
        return {"secret_id": self.secret_id, "key": self.key,
                "category": self.category, "created_at": self.created_at}


class SecretsManager:
    def __init__(self) -> None:
        self._secrets: Dict[str, SecretEntry] = {}
        self._access_log: List[Dict[str, Any]] = []

    def set_secret(self, key: str, value: str, category: str = "general") -> SecretEntry:
        entry = SecretEntry(key, value, category)
        self._secrets[key] = entry
        return entry

    def get_secret(self, key: str) -> Optional[str]:
        entry = self._secrets.get(key)
        if entry:
            self._access_log.append({"key": key, "time": time.time()})
            return entry._value
        return None

    def delete_secret(self, key: str) -> bool:
        if key in self._secrets:
            del self._secrets[key]
            return True
        return False

    def rotate_secret(self, key: str, new_value: str) -> bool:
        entry = self._secrets.get(key)
        if entry:
            entry._value = new_value
            entry.value_hash = hashlib.sha256(new_value.encode()).hexdigest()
            entry.rotated_at = time.time()
            return True
        return False

    def list_secrets(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        if category:
            return [e.to_dict() for e in self._secrets.values() if e.category == category]
        return [e.to_dict() for e in self._secrets.values()]

    def count(self) -> int:
        return len(self._secrets)

    def get_access_log(self) -> List[Dict[str, Any]]:
        return list(self._access_log)
