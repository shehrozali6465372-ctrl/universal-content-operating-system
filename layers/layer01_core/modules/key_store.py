"""
Key Store Module
Layer 1: Core System — Module 2 Support

Manages the .secrets file where encrypted values are stored.
Handles reading, writing, and file-level encryption.

File format: JSON with encrypted values
"""

import json
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
        """Load all secrets from file."""
        if not self._path.exists():
            return {}
        with open(self._path, "r") as f:
            return json.load(f)

    def save(self, secrets: Dict[str, str]) -> None:
        """Save all secrets to file with restrictive permissions."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(secrets, f, indent=2)
        # Set file permissions to owner-only (0600)
        try:
            self._path.chmod(0o600)
        except OSError:
            pass  # Windows or restricted environments

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
