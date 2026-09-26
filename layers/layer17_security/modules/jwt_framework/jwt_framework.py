"""Minimal fail-closed HS256 JWT implementation for internal UCOS contracts."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from typing import Any, Dict, Optional


class JWTToken:
    __slots__ = ("header", "payload", "signature", "raw")

    def __init__(self, header: Dict[str, Any], payload: Dict[str, Any],
                 signature: str = "") -> None:
        self.header = header
        self.payload = payload
        self.signature = signature
        self.raw = ""


class JWTFramework:
    def __init__(self, secret_key: str | None = None, issuer: str = "aios") -> None:
        if not secret_key or len(secret_key) < 32:
            raise ValueError("a strong JWT secret is required")
        self._secret = secret_key.encode("utf-8")
        self._issuer = issuer
        self._blacklist: set[str] = set()

    @staticmethod
    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    @staticmethod
    def _b64decode(value: str) -> bytes:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

    def create_token(self, payload: Dict[str, Any], expires_in: float = 3600.0,
                     issuer: str | None = None) -> str:
        if expires_in <= 0:
            raise ValueError("expires_in must be positive")
        header = {"alg": "HS256", "typ": "JWT"}
        now = int(time.time())
        payload_full = {**payload, "exp": now + int(expires_in), "iat": now,
                        "jti": uuid.uuid4().hex, "iss": issuer or self._issuer}
        header_b64 = self._b64url(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = self._b64url(json.dumps(payload_full, separators=(",", ":")).encode())
        message = f"{header_b64}.{payload_b64}"
        signature = self._b64url(hmac.new(self._secret, message.encode(), hashlib.sha256).digest())
        return f"{message}.{signature}"

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not token or token in self._blacklist:
            return None
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            header_b64, payload_b64, signature = parts
            header = json.loads(self._b64decode(header_b64))
            if header.get("alg") != "HS256" or header.get("typ") != "JWT":
                return None
            message = f"{header_b64}.{payload_b64}"
            expected = self._b64url(hmac.new(self._secret, message.encode(), hashlib.sha256).digest())
            if not hmac.compare_digest(signature, expected):
                return None
            payload = json.loads(self._b64decode(payload_b64))
            now = int(time.time())
            if payload.get("iss") != self._issuer or int(payload.get("exp", 0)) <= now:
                return None
            if int(payload.get("iat", now)) > now + 30:
                return None
            return payload
        except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError):
            return None

    def revoke_token(self, token: str) -> bool:
        if not token:
            return False
        self._blacklist.add(token)
        return True

    def is_revoked(self, token: str) -> bool:
        return token in self._blacklist

    def refresh_token(self, token: str, expires_in: float = 3600.0) -> Optional[str]:
        payload = self.decode_token(token)
        if not payload:
            return None
        self.revoke_token(token)
        new_payload = {k: v for k, v in payload.items() if k not in ("exp", "iat", "jti")}
        return self.create_token(new_payload, expires_in)

    def list_blacklist(self) -> int:
        return len(self._blacklist)

    def clear_blacklist(self) -> int:
        count = len(self._blacklist)
        self._blacklist.clear()
        return count
