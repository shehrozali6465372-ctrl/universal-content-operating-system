"""Authenticated encryption utilities for Layer 17."""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionEngine:
    def __init__(self) -> None:
        self._key: bytes | None = None

    def set_key(self, key: str) -> None:
        if not isinstance(key, str) or len(key) < 16:
            raise ValueError("encryption key material must be at least 16 characters")
        self._key = hashlib.sha256(key.encode("utf-8")).digest()

    def generate_key(self) -> str:
        key = secrets.token_bytes(32)
        return base64.urlsafe_b64encode(key).decode("ascii")

    def _require_key(self) -> bytes:
        if self._key is None:
            raise RuntimeError("encryption key is not configured")
        return self._key

    def encrypt(self, plaintext: str) -> str:
        key = self._require_key()
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        key = self._require_key()
        try:
            raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
            if len(raw) < 12 + 16:
                raise ValueError("ciphertext is too short")
            return AESGCM(key).decrypt(raw[:12], raw[12:], None).decode("utf-8")
        except (ValueError, UnicodeDecodeError, InvalidTag) as exc:
            raise ValueError("invalid or tampered ciphertext") from exc

    def hash(self, data: str, algorithm: str = "sha256") -> str:
        if algorithm == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()
        if algorithm == "sha512":
            return hashlib.sha512(data.encode()).hexdigest()
        raise ValueError("unsupported hash algorithm")

    def hmac_sign(self, message: str) -> str:
        return hmac.new(self._require_key(), message.encode(), hashlib.sha256).hexdigest()

    def hmac_verify(self, message: str, signature: str) -> bool:
        expected = self.hmac_sign(message)
        return hmac.compare_digest(expected, signature)
