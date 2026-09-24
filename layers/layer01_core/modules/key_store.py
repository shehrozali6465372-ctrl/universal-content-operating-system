"""
Key Store Module
Layer 1: Core System — Module 2 Support

Manages the .secrets file where encrypted values are stored.
Handles reading, writing, and file-level encryption.

File format: JSON with encrypted values
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional
from threading import RLock


class KeyStore:
    """Manages .secrets file for encrypted secret storage."""

    _locks = {}
    _locks_guard = RLock()

    def __init__(self, secrets_path: str = ".secrets"):
        self._path = Path(secrets_path)
        with self._locks_guard:
            self._lock = self._locks.setdefault(str(self._path.resolve()), RLock())

    @property
    def path(self) -> Path:
        return self._path

    @property
    def exists(self) -> bool:
        return self._path.exists()

    def load(self) -> Dict[str, str]:
        """Load all secrets from file.

        Corrupt or non-object JSON is a hard failure: silently treating it as
        an empty store could overwrite the remaining encrypted secrets.
        """
        with self._lock:
            return self._load_unlocked()

    def _load_unlocked(self) -> Dict[str, str]:
        if not self._path.exists():
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Unable to load secret store: {self._path}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"Secret store must contain a JSON object: {self._path}")
        if not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
            raise ValueError(f"Secret store contains invalid entries: {self._path}")
        return data

    def save(self, secrets: Dict[str, str]) -> None:
        """Atomically replace the secrets file with restrictive permissions."""
        with self._lock:
            self._save_unlocked(secrets)

    def _save_unlocked(self, secrets: Dict[str, str]) -> None:
        if not isinstance(secrets, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in secrets.items()
        ):
            raise TypeError("Secret store values must be a mapping of string names to strings")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self._path.parent),
            prefix=f".{self._path.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(secrets, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            try:
                os.chmod(tmp_name, 0o600)
            except OSError:
                pass  # Windows or restricted environments
            os.replace(tmp_name, self._path)
            try:
                self._path.chmod(0o600)
            except OSError:
                pass
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def add(self, name: str, encrypted_value: str) -> None:
        """Add or update a single secret atomically within this process."""
        with self._lock:
            secrets = self._load_unlocked()
            secrets[name] = encrypted_value
            self._save_unlocked(secrets)

    def remove(self, name: str) -> bool:
        """Remove a secret atomically within this process."""
        with self._lock:
            secrets = self._load_unlocked()
            if name in secrets:
                del secrets[name]
                self._save_unlocked(secrets)
                return True
            return False

    def get(self, name: str) -> Optional[str]:
        """Get encrypted value by name."""
        with self._lock:
            return self._load_unlocked().get(name)

    def has(self, name: str) -> bool:
        """Check if secret exists."""
        with self._lock:
            return name in self._load_unlocked()

    def names(self) -> list:
        """Return list of secret names (no values)."""
        with self._lock:
            return list(self._load_unlocked().keys())

    def count(self) -> int:
        """Return total number of stored secrets."""
        with self._lock:
            return len(self._load_unlocked())

    def clear(self) -> None:
        """Remove all secrets from file."""
        with self._lock:
            self._save_unlocked({})
