"""persistence_security.py — Persistence security."""
from __future__ import annotations
import hashlib
from typing import Any, Dict, List


class PersistenceSecurity:
    """Security layer for persistence."""

    def __init__(self) -> None:
        self._allowed_origins: List[str] = []
        self._blocked_patterns: List[str] = []
        self._audit_log: List[Dict[str, Any]] = []

    def allow_origin(self, origin: str) -> None:
        self._allowed_origins.append(origin)

    def block_pattern(self, pattern: str) -> None:
        self._blocked_patterns.append(pattern)

    def is_allowed(self, origin: str) -> bool:
        if self._blocked_patterns:
            for p in self._blocked_patterns:
                if p in origin:
                    return False
        return not self._allowed_origins or origin in self._allowed_origins

    def audit(self, action: str, user: str, details: Dict[str, Any] = None) -> None:
        self._audit_log.append({"action": action, "user": user,
                                 "details": details or {}})

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._audit_log[-limit:]

    def hash_data(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def stats(self) -> Dict[str, Any]:
        return {"allowed_origins": len(self._allowed_origins),
                "blocked_patterns": len(self._blocked_patterns),
                "audit_entries": len(self._audit_log)}
