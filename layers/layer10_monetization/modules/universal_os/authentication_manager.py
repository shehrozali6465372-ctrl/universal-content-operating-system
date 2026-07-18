"""AuthenticationManager — API keys, tokens, roles, permissions, sessions."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_AM_COUNTER = itertools.count(1)

ROLES = ("admin", "user", "viewer", "api_only", "limited")


class AuthToken:
    """An authentication token."""

    __slots__ = ("token_id", "user_id", "role", "permissions",
                 "created_at", "expires_at", "active")

    def __init__(self, user_id: str = "", role: str = "user") -> None:
        self.token_id: str = f"tok_{next(_AM_COUNTER)}"
        self.user_id = user_id
        self.role = role if role in ROLES else "user"
        self.permissions: List[str] = []
        self.created_at: float = time.time()
        self.expires_at: float = time.time() + 86400
        self.active: bool = True

    def is_valid(self) -> bool:
        return self.active and time.time() < self.expires_at

    def has_permission(self, permission: str) -> bool:
        if self.role == "admin":
            return True
        return permission in self.permissions

    def to_dict(self) -> Dict[str, Any]:
        return {"token_id": self.token_id, "user_id": self.user_id,
                "role": self.role, "active": self.active}


class AuthenticationManager:
    """Manage API keys, tokens, roles, permissions, and sessions."""

    def __init__(self) -> None:
        self._tokens: Dict[str, AuthToken] = {}
        self._api_keys: Dict[str, str] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_token(self, user_id: str, role: str = "user",
                     permissions: Optional[List[str]] = None,
                     ttl_hours: int = 24) -> AuthToken:
        token = AuthToken(user_id, role)
        if permissions:
            token.permissions = list(permissions)
        token.expires_at = time.time() + ttl_hours * 3600
        self._tokens[token.token_id] = token
        return token

    def validate_token(self, token_id: str) -> bool:
        token = self._tokens.get(token_id)
        return token is not None and token.is_valid()

    def revoke_token(self, token_id: str) -> bool:
        token = self._tokens.get(token_id)
        if token:
            token.active = False
            return True
        return False

    def create_api_key(self, name: str) -> str:
        import hashlib
        key = hashlib.sha256(f"{name}_{time.time()}".encode()).hexdigest()[:32]
        self._api_keys[key] = name
        return key

    def validate_api_key(self, key: str) -> bool:
        return key in self._api_keys

    def create_session(self, user_id: str) -> str:
        import hashlib
        session_id = hashlib.sha256(f"{user_id}_{time.time()}".encode()).hexdigest()[:16]
        self._sessions[session_id] = {"user_id": user_id, "created_at": time.time()}
        return session_id

    def validate_session(self, session_id: str) -> bool:
        return session_id in self._sessions

    def destroy_session(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def get_token(self, token_id: str) -> Optional[AuthToken]:
        return self._tokens.get(token_id)

    def get_stats(self) -> Dict[str, Any]:
        active = sum(1 for t in self._tokens.values() if t.is_valid())
        return {"total_tokens": len(self._tokens), "active_tokens": active,
                "api_keys": len(self._api_keys), "sessions": len(self._sessions)}
