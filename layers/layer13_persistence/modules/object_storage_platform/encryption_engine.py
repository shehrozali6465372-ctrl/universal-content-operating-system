"""encryption_engine.py — Data encryption support."""
from __future__ import annotations
import hashlib


class EncryptionEngine:
    """Encrypts and decrypts data."""

    def __init__(self, algorithm: str = "aes256") -> None:
        self._algorithm = algorithm

    def encrypt(self, data: bytes, key: str = "") -> bytes:
        key_hash = hashlib.sha256(key.encode()).digest() if key else b"\x00" * 32
        return bytes(b ^ key_hash[i % 32] for i, b in enumerate(data))

    def decrypt(self, data: bytes, key: str = "") -> bytes:
        return self.encrypt(data, key)

    def hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def get_algorithm(self) -> str:
        return self._algorithm
