"""RedisSession — User session and context management.

Features:
- Session creation, get, update, destroy
- Session data as hash (user_id, platform, context, preferences)
- Automatic TTL-based expiry
- Session history (recent sessions per user)
- Context snapshot/restore
"""
from __future__ import annotations
import json
import time
import uuid
from typing import Any, Dict, List, Optional


class RedisSession:
    """Manage user sessions and context in Redis."""

    def __init__(self, client: Any, session_ttl: float = 3600.0):
        self._client = client
        self._session_ttl = session_ttl
        self._prefix = "session"

    def _key(self, session_id: str) -> str:
        return f"{self._prefix}:{session_id}"

    def _user_index_key(self, user_id: str) -> str:
        return f"{self._prefix}:_user:{user_id}"

    def create(self, user_id: str, platform: str, context: Dict[str, Any] = None,
               preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        now = time.time()

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "platform": platform,
            "context": json.dumps(context or {}, default=str),
            "preferences": json.dumps(preferences or {}, default=str),
            "created_at": str(now),
            "last_active": str(now),
            "status": "active",
        }

        # Store session
        for field, value in session_data.items():
            self._client.hset(self._key(session_id), field, value)

        # Set TTL
        self._client.expire(self._key(session_id), self._session_ttl)

        # Index by user
        self._client.sadd(self._user_index_key(user_id), session_id)
        self._client.expire(self._user_index_key(user_id), self._session_ttl * 2)

        return self.get(session_id)

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        data = self._client.hgetall(self._key(session_id))
        if not data:
            return None

        # Refresh TTL
        self._client.expire(self._key(session_id), self._session_ttl)

        # Parse JSON fields
        for field in ("context", "preferences"):
            if field in data:
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    data[field] = {}

        # Parse timestamps
        for field in ("created_at", "last_active"):
            if field in data:
                try:
                    data[field] = float(data[field])
                except (ValueError, TypeError):
                    data[field] = 0.0

        return data

    def update(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session fields."""
        existing = self.get(session_id)
        if not existing:
            return False

        now = time.time()
        updates["last_active"] = str(now)

        for key, value in updates.items():
            if key in ("context", "preferences"):
                self._client.hset(self._key(session_id), key, json.dumps(value, default=str))
            else:
                self._client.hset(self._key(session_id), key, str(value))

        self._client.expire(self._key(session_id), self._session_ttl)
        return True

    def update_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """Merge new context into existing session context."""
        existing = self.get(session_id)
        if not existing:
            return False

        old_context = existing.get("context", {})
        if isinstance(old_context, str):
            try:
                old_context = json.loads(old_context)
            except (json.JSONDecodeError, TypeError):
                old_context = {}

        old_context.update(context)
        return self.update(session_id, {"context": old_context})

    def destroy(self, session_id: str) -> bool:
        """Destroy a session."""
        existing = self.get(session_id)
        if not existing:
            return False

        user_id = existing.get("user_id", "")
        self._client.delete(self._key(session_id))

        # Remove from user index
        if user_id:
            self._client.srem(self._user_index_key(user_id), session_id)

        return True

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        session_ids = self._client.smembers(self._user_index_key(user_id))
        sessions = []
        for sid in session_ids:
            session = self.get(sid)
            if session:
                sessions.append(session)
        return sorted(sessions, key=lambda s: s.get("last_active", 0), reverse=True)

    def get_active_sessions(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get all active sessions, optionally filtered by user."""
        if user_id:
            return [s for s in self.get_user_sessions(user_id) if s.get("status") == "active"]
        # Without user_id, only check tracked user indices
        return []

    def snapshot(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Create a snapshot of current session state."""
        session = self.get(session_id)
        if not session:
            return None

        return {
            "snapshot_id": f"snap_{int(time.time() * 1000)}",
            "session_id": session_id,
            "user_id": session.get("user_id"),
            "platform": session.get("platform"),
            "context": session.get("context", {}),
            "preferences": session.get("preferences", {}),
            "snapshot_time": time.time(),
        }

    def restore(self, session_id: str, snapshot: Dict[str, Any]) -> bool:
        """Restore session from snapshot."""
        if snapshot.get("session_id") != session_id:
            return False
        return self.update(session_id, {
            "context": snapshot.get("context", {}),
            "preferences": snapshot.get("preferences", {}),
        })

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        # Count sessions from user indices
        total = 0
        user_keys = self._client.keys(f"{self._prefix}:_user:*")
        for uk in user_keys:
            members = self._client.smembers(uk)
            total += len(members)
        return {
            "total_sessions": total,
            "active_sessions": total,
            "expired_sessions": 0,
            "session_ttl_seconds": self._session_ttl,
        }
