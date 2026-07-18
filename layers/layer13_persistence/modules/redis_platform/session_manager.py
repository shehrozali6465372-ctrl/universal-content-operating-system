"""session_manager.py — Session management with Redis."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional


class Session:
    """User session."""
    __slots__ = ("session_id", "user_id", "data", "created_at", "last_accessed", "ttl")
    _counter = 0

    def __init__(self, session_id: str, user_id: str, ttl: float = 3600.0) -> None:
        Session._counter += 1
        self.session_id = session_id
        self.user_id = user_id
        self.data: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.last_accessed: float = time.time()
        self.ttl = ttl

    def is_expired(self) -> bool:
        return (time.time() - self.last_accessed) > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {"session_id": self.session_id, "user_id": self.user_id,
                "data": dict(self.data), "expired": self.is_expired()}


class SessionManager:
    """Manages user sessions."""

    def __init__(self, default_ttl: float = 3600.0) -> None:
        self._sessions: Dict[str, Session] = {}
        self._default_ttl = default_ttl

    def create(self, session_id: str, user_id: str) -> Session:
        session = Session(session_id, user_id, self._default_ttl)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        session = self._sessions.get(session_id)
        if session and not session.is_expired():
            session.last_accessed = time.time()
            return session
        return None

    def destroy(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def get_user_sessions(self, user_id: str) -> list:
        return [s for s in self._sessions.values() if s.user_id == user_id]

    def cleanup_expired(self) -> int:
        expired = [k for k, s in self._sessions.items() if s.is_expired()]
        for k in expired:
            del self._sessions[k]
        return len(expired)

    def active_count(self) -> int:
        return len(self._sessions)

    def to_dict(self) -> Dict[str, Any]:
        return {"active": self.active_count(), "default_ttl": self._default_ttl}
