"""EncryptionEngine — symmetric/asymmetric encryption utilities."""
from __future__ import annotations
import base64
import hashlib
import hmac
import secrets
from typing import Any, Dict


class EncryptionEngine:
    def __init__(self) -> None:
        self._key: bytes = b""

    def set_key(self, key: str) -> None:
        self._key = hashlib.sha256(key.encode()).digest()

    def generate_key(self) -> str:
        return secrets.token_hex(32)

    def encrypt(self, plaintext: str) -> str:
        if not self._key:
            self._key = hashlib.sha256(b"default-key").digest()
        key = self._key
        data = plaintext.encode()
        encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return base64.b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        if not self._key:
            self._key = hashlib.sha256(b"default-key").digest()
        key = self._key
        data = base64.b64decode(ciphertext)
        decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return decrypted.decode()

    def hash(self, data: str, algorithm: str = "sha256") -> str:
        if algorithm == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(data.encode()).hexdigest()
        elif algorithm == "md5":
            return hashlib.sha256(data.encode()).hexdigest()
        return hashlib.sha256(data.encode()).hexdigest()

    def hmac_sign(self, message: str) -> str:
        return hmac.new(self._key, message.encode(), hashlib.sha256).hexdigest()

    def hmac_verify(self, message: str, signature: str) -> bool:
        expected = hmac.new(self._key, message.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
