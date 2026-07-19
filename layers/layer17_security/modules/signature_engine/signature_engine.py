"""SignatureEngine — digital signature creation and verification."""
from __future__ import annotations
import hashlib
import hmac
import secrets
from typing import Any, Dict


class SignatureEngine:
    def __init__(self) -> None:
        self._keys: Dict[str, bytes] = {}

    def generate_key(self, key_name: str) -> str:
        key = secrets.token_bytes(32)
        self._keys[key_name] = key
        return key.hex()

    def sign(self, key_name: str, data: str) -> str:
        key = self._keys.get(key_name, b"default")
        return hmac.new(key, data.encode(), hashlib.sha256).hexdigest()

    def verify(self, key_name: str, data: str, signature: str) -> bool:
        key = self._keys.get(key_name, b"default")
        expected = hmac.new(key, data.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def list_keys(self) -> list:
        return list(self._keys.keys())

    def remove_key(self, key_name: str) -> bool:
        if key_name in self._keys:
            del self._keys[key_name]
            return True
        return False
