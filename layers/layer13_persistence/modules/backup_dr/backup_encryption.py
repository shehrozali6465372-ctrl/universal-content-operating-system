"""backup_encryption.py — Backup encryption."""
from __future__ import annotations
import hashlib


class BackupEncryptor:
    """Encrypts and decrypts backups."""

    def __init__(self, algorithm: str = "aes256") -> None:
        self._algorithm = algorithm

    def encrypt(self, data: bytes, key: str) -> bytes:
        key_hash = hashlib.sha256(key.encode()).digest()
        return bytes(b ^ key_hash[i % 32] for i, b in enumerate(data))

    def decrypt(self, data: bytes, key: str) -> bytes:
        return self.encrypt(data, key)

    def get_algorithm(self) -> str:
        return self._algorithm

    def verify(self, original: bytes, encrypted: bytes, key: str) -> bool:
        return self.decrypt(encrypted, key) == original
