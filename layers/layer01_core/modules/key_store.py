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


class KeyStore:
    """Manages .secrets file for encrypted secret storage."""

    def __init__(self, secrets_path: str = ".secrets"):
        self._path = Path(secrets_path)

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
        """Add or update a single secret."""
        secrets = self.load()
        secrets[name] = encrypted_value
        self.save(secrets)

    def remove(self, name: str) -> bool:
        """Remove a secret. Returns True if found and removed."""
        secrets = self.load()
        if name in secrets:
            del secrets[name]
            self.save(secrets)
            return True
        return False

    def get(self, name: str) -> Optional[str]:
        """Get encrypted value by name."""
        secrets = self.load()
        return secrets.get(name)

    def has(self, name: str) -> bool:
        """Check if secret exists."""
        return name in self.load()

    def names(self) -> list:
        """Return list of secret names (no values)."""
        return list(self.load().keys())

    def count(self) -> int:
        """Return total number of stored secrets."""
        return len(self.load())

    def clear(self) -> None:
        """Remove all secrets from file."""
        self.save({})
