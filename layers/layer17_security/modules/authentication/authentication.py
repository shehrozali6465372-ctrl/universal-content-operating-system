"""Production authentication primitives for Layer 17."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional


class AuthStrategy(str, Enum):
    PASSWORD = "password"
    API_KEY = "api_key"
    TOKEN = "token"
    OAUTH = "oauth"


class User:
    __slots__ = ("user_id", "username", "email", "password_hash", "salt",
                 "roles", "is_active", "created_at", "last_login", "metadata")

    def __init__(self, username: str, email: str = "", password: str = "") -> None:
        if not username:
            raise ValueError("username is required")
        self.user_id = uuid.uuid4().hex
        self.username = username
        self.email = email
        self.salt = secrets.token_bytes(16)
        self.password_hash = self._hash_password(password) if password else ""
        self.roles: List[str] = []
        self.is_active = True
        self.created_at = time.time()
        self.last_login = 0.0
        self.metadata: Dict[str, Any] = {}

    def _hash_password(self, password: str) -> bytes:
        if not isinstance(password, str):
            raise TypeError("password must be a string")
        return hashlib.pbkdf2_hmac("sha256", password.encode(), self.salt, 600_000)

    def verify_password(self, password: str) -> bool:
        return bool(self.password_hash) and hmac.compare_digest(
            self._hash_password(password), self.password_hash
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"user_id": self.user_id, "username": self.username,
                "email": self.email, "is_active": self.is_active,
                "roles": list(self.roles)}


class AuthSession:
    __slots__ = ("session_id", "user_id", "token", "created_at",
                 "expires_at", "ip_address", "metadata")

    def __init__(self, user_id: str, token: str, expires_in: float = 3600.0) -> None:
        if expires_in <= 0:
            raise ValueError("expires_in must be positive")
        self.session_id = uuid.uuid4().hex
        self.user_id = user_id
        self.token = token
        self.created_at = time.time()
        self.expires_at = self.created_at + expires_in
        self.ip_address = ""
        self.metadata: Dict[str, Any] = {}

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {"session_id": self.session_id, "user_id": self.user_id,
                "expires_at": self.expires_at}


class AuthenticationManager:
    def __init__(self, max_failed: int = 5) -> None:
        if max_failed <= 0:
            raise ValueError("max_failed must be positive")
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, AuthSession] = {}
        self._api_keys: Dict[str, str] = {}
        self._failed_attempts: Dict[str, int] = {}
        self._max_failed = max_failed

    def register_user(self, username: str, email: str = "",
                      password: str = "") -> User:
        if not password:
            raise ValueError("password is required")
        if any(u.username == username for u in self._users.values()):
            raise ValueError("username already exists")
        user = User(username, email, password)
        self._users[user.user_id] = user
        return user

    def authenticate_password(self, username: str, password: str) -> Optional[AuthSession]:
        user = next((u for u in self._users.values() if u.username == username), None)
        if user is None or not user.is_active:
            return None
        if not user.verify_password(password):
            self._failed_attempts[username] = self._failed_attempts.get(username, 0) + 1
            if self._failed_attempts[username] >= self._max_failed:
                user.is_active = False
            return None
        self._failed_attempts.pop(username, None)
        token = secrets.token_urlsafe(32)
        session = AuthSession(user.user_id, token)
        self._sessions[session.session_id] = session
        user.last_login = time.time()
        return session

    def register_api_key(self, user_id: str, api_key: str) -> bool:
        if user_id not in self._users or not api_key:
            return False
        self._api_keys[hashlib.sha256(api_key.encode()).hexdigest()] = user_id
        return True

    def authenticate_api_key(self, api_key: str) -> Optional[str]:
        if not api_key:
            return None
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return self._api_keys.get(key_hash)

    def validate_session(self, session_id: str) -> Optional[AuthSession]:
        session = self._sessions.get(session_id)
        if session and not session.is_expired():
            return session
        if session:
            self._sessions.pop(session_id, None)
        return None

    def invalidate_session(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def list_users(self) -> List[Dict[str, Any]]:
        return [u.to_dict() for u in self._users.values()]

    def stats(self) -> Dict[str, Any]:
        return {"users": len(self._users), "sessions": len(self._sessions),
                "api_keys": len(self._api_keys)}
