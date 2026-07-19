"""JWTFramework — JSON Web Token creation and validation."""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Dict, List, Optional


class JWTToken:
    __slots__ = ("header", "payload", "signature", "raw")

    def __init__(self, header: Dict[str, Any], payload: Dict[str, Any],
                 signature: str = "") -> None:
        self.header = header
        self.payload = payload
        self.signature = signature
        self.raw = ""


class JWTFramework:
    def __init__(self, secret_key: str = "default-secret") -> None:
        self._secret = secret_key.encode()
        self._blacklist: set = set()

    def _b64url(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

    def create_token(self, payload: Dict[str, Any], expires_in: float = 3600.0,
                     issuer: str = "aios") -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        payload_full = {**payload, "exp": time.time() + expires_in,
                        "iat": time.time(), "jti": str(uuid.uuid4())[:8],
                        "iss": issuer}
        header_b64 = self._b64url(json.dumps(header).encode())
        payload_b64 = self._b64url(json.dumps(payload_full).encode())
        message = f"{header_b64}.{payload_b64}"
        signature = self._b64url(hmac.new(self._secret, message.encode(), hashlib.sha256).digest())
        return f"{header_b64}.{payload_b64}.{signature}"

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        if token in self._blacklist:
            return None
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature = parts
        message = f"{header_b64}.{payload_b64}"
        expected_sig = self._b64url(hmac.new(self._secret, message.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected_sig):
            return None
        padding = 4 - len(payload_b64) % 4
        payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload

    def revoke_token(self, token: str) -> bool:
        self._blacklist.add(token)
        return True

    def is_revoked(self, token: str) -> bool:
        return token in self._blacklist

    def refresh_token(self, token: str, expires_in: float = 3600.0) -> Optional[str]:
        payload = self.decode_token(token)
        if not payload:
            return None
        self.revoke_token(token)
        new_payload = {k: v for k, v in payload.items()
                       if k not in ("exp", "iat", "jti")}
        return self.create_token(new_payload, expires_in)

    def list_blacklist(self) -> int:
        return len(self._blacklist)

    def clear_blacklist(self) -> int:
        count = len(self._blacklist)
        self._blacklist.clear()
        return count
