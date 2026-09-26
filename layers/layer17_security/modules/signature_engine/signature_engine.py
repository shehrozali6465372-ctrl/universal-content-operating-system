"""HMAC signature engine with fail-closed key handling."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Dict


class SignatureEngine:
    def __init__(self) -> None:
        self._keys: Dict[str, bytes] = {}

    def generate_key(self, key_name: str) -> str:
        if not key_name:
            raise ValueError("key_name is required")
        key = secrets.token_bytes(32)
        self._keys[key_name] = key
        return key.hex()

    def sign(self, key_name: str, data: str) -> str:
        key = self._keys.get(key_name)
        if key is None:
            raise KeyError("signing key is not configured")
        return hmac.new(key, data.encode(), hashlib.sha256).hexdigest()

    def verify(self, key_name: str, data: str, signature: str) -> bool:
        key = self._keys.get(key_name)
        if key is None or not signature:
            return False
        expected = hmac.new(key, data.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def list_keys(self) -> list[str]:
        return list(self._keys.keys())

    def remove_key(self, key_name: str) -> bool:
        return self._keys.pop(key_name, None) is not None
