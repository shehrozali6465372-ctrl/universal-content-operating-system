"""
Audit Logger Module
Layer 1: Core System — Module 2 Support

Logs all secret-related actions with timestamps.
NEVER logs secret values — only action names and status.

Usage:
    from layers.layer01_core.modules.audit_logger import AuditLogger

    audit = AuditLogger(log_path="logs/audit.log")
    audit.log("OPENAI_API_KEY", "CREATED", "SUCCESS")
    audit.log("FACEBOOK_TOKEN", "ACCESSED", "DENIED")
"""

import json
import os
from threading import RLock
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from enum import Enum


class AuditAction(str, Enum):
    CREATED = "CREATED"
    ACCESSED = "ACCESSED"
    DELETED = "DELETED"
    ROTATED = "ROTATED"
    FAILED_ACCESS = "FAILED_ACCESS"
    HEALTH_CHECK = "HEALTH_CHECK"


class AuditStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DENIED = "DENIED"


class AuditLogger:
    """Writes audit logs for secret operations. Never stores values."""

    _locks = {}
    _locks_guard = RLock()

    def __init__(self, log_path: str = "logs/audit.log"):
        self._log_path = Path(log_path).resolve()
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._locks_guard:
            self._lock = self._locks.setdefault(str(self._log_path), RLock())

    def log(
        self,
        secret_name: str,
        action: str,
        status: str,
        details: Optional[str] = None,
    ) -> dict:
        """Write a single audit entry. Returns the entry dict."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "secret_name": secret_name,
            "action": action,
            "status": status,
        }
        if details:
            entry["details"] = " ".join(str(details).split())[:500]

        with self._lock:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
                os.fsync(f.fileno())

        return entry

    def get_logs(self, limit: int = 50) -> list:
        """Read last N audit entries."""
        with self._lock:
            if not self._log_path.exists():
                return []
            entries = []
        with open(self._log_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return entries[-limit:]

    def get_logs_for_secret(self, secret_name: str) -> list:
        """Get audit entries for a specific secret."""
        return [
            e for e in self.get_logs(limit=1000)
            if e.get("secret_name") == secret_name
        ]

    def count_actions(self) -> dict:
        """Count total actions by type."""
        counts = {}
        for entry in self.get_logs(limit=10000):
            action = entry.get("action", "UNKNOWN")
            counts[action] = counts.get(action, 0) + 1
        return counts

    def clear(self) -> None:
        """Clear audit log (use carefully)."""
        with self._lock:
            if self._log_path.exists():
                with open(self._log_path, "w", encoding="utf-8") as f:
                    f.flush()
                    os.fsync(f.fileno())
