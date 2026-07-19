"""Authentication — user authentication with multiple strategies."""
from __future__ import annotations
import hashlib
import hmac
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class AuthStrategy(str, Enum):
    PASSWORD = "password"; API_KEY = "api_key"; TOKEN = "token"; OAUTH = "oauth"


class User:
    __slots__ = ("user_id", "username", "email", "password_hash", "salt",
                 "roles", "is_active", "created_at", "last_login", "metadata")

    def __init__(self, username: str, email: str = "", password: str = "") -> None:
        self.user_id = str(uuid.uuid4())[:12]
        self.username = username
        self.email = email
        self.salt = str(uuid.uuid4())[:8]
        self.password_hash = self._hash_password(password) if password else ""
        self.roles: List[str] = []
        self.is_active = True
        self.created_at = time.time()
        self.last_login: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256((password + self.salt).encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        return self._hash_password(password) == self.password_hash

    def to_dict(self) -> Dict[str, Any]:
        return {"user_id": self.user_id, "username": self.username,
                "email": self.email, "is_active": self.is_active,
                "roles": self.roles}


class AuthSession:
    __slots__ = ("session_id", "user_id", "token", "created_at",
                 "expires_at", "ip_address", "metadata")

    def __init__(self, user_id: str, token: str, expires_in: float = 3600.0) -> None:
        self.session_id = str(uuid.uuid4())[:12]
        self.user_id = user_id
        self.token = token
        self.created_at = time.time()
        self.expires_at = time.time() + expires_in
        self.ip_address = ""
        self.metadata: Dict[str, Any] = {}

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {"session_id": self.session_id, "user_id": self.user_id,
                "expires_at": self.expires_at}


class AuthenticationManager:
    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, AuthSession] = {}
        self._api_keys: Dict[str, str] = {}
        self._failed_attempts: Dict[str, int] = {}
        self._max_failed = 5

    def register_user(self, username: str, email: str = "",
                      password: str = "") -> User:
        user = User(username, email, password)
        self._users[user.user_id] = user
        return user

    def authenticate_password(self, username: str, password: str) -> Optional[AuthSession]:
        user = None
        for u in self._users.values():
            if u.username == username:
                user = u
                break
        if not user or not user.is_active:
            return None
        if not user.verify_password(password):
            self._failed_attempts[username] = self._failed_attempts.get(username, 0) + 1
            if self._failed_attempts[username] >= self._max_failed:
                user.is_active = False
            return None
        self._failed_attempts.pop(username, None)
        token = str(uuid.uuid4())
        session = AuthSession(user.user_id, token)
        self._sessions[session.session_id] = session
        user.last_login = time.time()
        return session

    def register_api_key(self, user_id: str, api_key: str) -> bool:
        if user_id in self._users:
            self._api_keys[api_key] = user_id
            return True
        return False

    def authenticate_api_key(self, api_key: str) -> Optional[str]:
        return self._api_keys.get(api_key)

    def validate_session(self, session_id: str) -> Optional[AuthSession]:
        session = self._sessions.get(session_id)
        if session and not session.is_expired():
            return session
        if session:
            del self._sessions[session_id]
        return None

    def invalidate_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def list_users(self) -> List[Dict[str, Any]]:
        return [u.to_dict() for u in self._users.values()]

    def stats(self) -> Dict[str, Any]:
        return {"users": len(self._users), "sessions": len(self._sessions),
                "api_keys": len(self._api_keys)}
