"""AuthenticationManager — non-predictable credentials with expiry and revocation."""
from __future__ import annotations
import hashlib
import hmac
import secrets
import threading
import time
from typing import Any, Dict, List, Optional

ROLES = ("admin", "user", "viewer", "api_only", "limited")


class AuthToken:
    """An authentication token record."""

    def __init__(self, user_id: str = "", role: str = "user") -> None:
        self.token_id = secrets.token_urlsafe(32)
        self.user_id = user_id
        self.role = role if role in ROLES else "user"
        self.permissions: List[str] = []
        self.created_at = time.time()
        self.expires_at = self.created_at + 86400
        self.active = True

    def is_valid(self) -> bool:
        return self.active and time.time() < self.expires_at

    def has_permission(self, permission: str) -> bool:
        return self.role == "admin" or permission in self.permissions

    def to_dict(self) -> Dict[str, Any]:
        return {"token_id": self.token_id, "user_id": self.user_id,
                "role": self.role, "active": self.active}


class AuthenticationManager:
    """Manage tokens, API keys, and expiring sessions."""

    def __init__(self, max_records: int = 10000) -> None:
        if max_records <= 0:
            raise ValueError("max_records must be positive")
        self._max_records = max_records
        self._tokens: Dict[str, AuthToken] = {}
        self._api_keys: Dict[str, str] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def _prune_expired(self) -> None:
        now = time.time()
        expired_tokens = [
            key for key, token in self._tokens.items()
            if token.expires_at <= now or not token.active
        ]
        for key in expired_tokens:
            self._tokens.pop(key, None)
        expired_sessions = [
            key for key, record in self._sessions.items()
            if record["expires_at"] <= now
        ]
        for key in expired_sessions:
            self._sessions.pop(key, None)
        while len(self._tokens) > self._max_records:
            self._tokens.pop(next(iter(self._tokens)))
        while len(self._api_keys) > self._max_records:
            self._api_keys.pop(next(iter(self._api_keys)))
        while len(self._sessions) > self._max_records:
            self._sessions.pop(next(iter(self._sessions)))

    def create_token(
        self, user_id: str, role: str = "user",
        permissions: Optional[List[str]] = None, ttl_hours: int = 24,
    ) -> AuthToken:
        if not user_id:
            raise ValueError("user_id is required")
        if ttl_hours <= 0:
            raise ValueError("ttl_hours must be positive")
        token = AuthToken(user_id, role)
        token.permissions = list(permissions or [])
        token.expires_at = time.time() + ttl_hours * 3600
        with self._lock:
            self._prune_expired()
            self._tokens[token.token_id] = token
        return token

    def validate_token(self, token_id: str) -> bool:
        with self._lock:
            token = self._tokens.get(token_id)
            return token is not None and token.is_valid()

    def revoke_token(self, token_id: str) -> bool:
        with self._lock:
            token = self._tokens.get(token_id)
            if token is None:
                return False
            token.active = False
            return True

    def create_api_key(self, name: str) -> str:
        if not name:
            raise ValueError("name is required")
        raw = secrets.token_urlsafe(32)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        with self._lock:
            self._prune_expired()
            self._api_keys[digest] = name
        return raw

    def validate_api_key(self, key: str) -> bool:
        if not key:
            return False
        digest = hashlib.sha256(key.encode()).hexdigest()
        with self._lock:
            return any(hmac.compare_digest(stored, digest) for stored in self._api_keys)

    def revoke_api_key(self, key: str) -> bool:
        if not key:
            return False
        digest = hashlib.sha256(key.encode()).hexdigest()
        with self._lock:
            return self._api_keys.pop(digest, None) is not None

    def create_session(self, user_id: str, ttl_hours: int = 24) -> str:
        if not user_id or ttl_hours <= 0:
            raise ValueError("valid user_id and positive ttl_hours are required")
        session_id = secrets.token_urlsafe(24)
        now = time.time()
        with self._lock:
            self._prune_expired()
            self._sessions[hashlib.sha256(session_id.encode()).hexdigest()] = {
                "user_id": user_id, "created_at": now, "expires_at": now + ttl_hours * 3600,
            }
        return session_id

    def validate_session(self, session_id: str) -> bool:
        if not session_id:
            return False
        with self._lock:
            record = self._sessions.get(hashlib.sha256(session_id.encode()).hexdigest())
            return record is not None and time.time() < record["expires_at"]

    def destroy_session(self, session_id: str) -> bool:
        if not session_id:
            return False
        with self._lock:
            return self._sessions.pop(
                hashlib.sha256(session_id.encode()).hexdigest(), None
            ) is not None

    def get_token(self, token_id: str) -> Optional[AuthToken]:
        with self._lock:
            return self._tokens.get(token_id)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            self._prune_expired()
            now = time.time()
            active = sum(1 for token in self._tokens.values()
                     if token.active and token.expires_at > now)
            sessions = sum(
                1 for record in self._sessions.values()
                if record["expires_at"] > now
            )
            return {
                "total_tokens": len(self._tokens),
                "active_tokens": active,
                "api_keys": len(self._api_keys),
                "sessions": sessions,
            }
