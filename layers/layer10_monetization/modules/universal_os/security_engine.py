"""SecurityEngine — bounded rate limiting and input-abuse detection."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class SecurityEngine:
    """Protect system from rate-limit abuse, spam, injection, and prompt attacks."""

    def __init__(self, rate_limit: int = 60, window_seconds: int = 60,
                 max_violations: int = 10000) -> None:
        if rate_limit <= 0 or window_seconds <= 0 or max_violations <= 0:
            raise ValueError("security limits must be positive")
        self._rate_limit = rate_limit
        self._window_seconds = window_seconds
        self._request_log: Dict[str, List[float]] = {}
        self._blocked: Dict[str, float] = {}
        self._violations: List[Dict[str, Any]] = []
        self._max_violations = max_violations
        self._blocked_patterns = [
            "ignore previous instructions", "ignore all previous",
            "you are now", "forget everything", "system prompt",
        ]

    def check_rate_limit(self, client_id: str) -> bool:
        if not client_id or self.is_blocked(client_id):
            return False
        now = time.time()
        requests = [timestamp for timestamp in self._request_log.get(client_id, [])
                    if now - timestamp < self._window_seconds]
        if len(requests) >= self._rate_limit:
            self._request_log[client_id] = requests
            self._record_violation(client_id, "rate_limit_exceeded")
            return False
        requests.append(now)
        self._request_log[client_id] = requests
        return True

    def is_blocked(self, client_id: str) -> bool:
        expires = self._blocked.get(client_id)
        if expires is None:
            return False
        if time.time() >= expires:
            self._blocked.pop(client_id, None)
            return False
        return True

    def block(self, client_id: str, duration_seconds: int = 300) -> None:
        if not client_id or duration_seconds <= 0:
            raise ValueError("client_id and positive duration are required")
        self._blocked[client_id] = time.time() + duration_seconds

    def unblock(self, client_id: str) -> bool:
        return self._blocked.pop(client_id, None) is not None

    def detect_injection(self, text: str) -> bool:
        text_lower = text.lower()
        for pattern in self._blocked_patterns:
            if pattern in text_lower:
                self._record_violation("input", "injection_attempt")
                return True
        return False

    def detect_spam(self, text: str, threshold: int = 10) -> bool:
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        words = text.split()
        repetitive = len(words) > 20 and len(set(word.lower() for word in words)) < len(words) * 0.2
        if len(words) > max(500, threshold):
            self._record_violation("input", "potential_spam")
            return True
        if repetitive:
            self._record_violation("input", "repetitive_content")
            return True
        return False

    def _record_violation(self, source: str, violation_type: str) -> None:
        self._violations.append({"source": source, "type": violation_type, "timestamp": time.time()})
        if len(self._violations) > self._max_violations:
            del self._violations[:-self._max_violations]

    def get_violations(self, violation_type: str = "") -> List[Dict[str, Any]]:
        if not violation_type:
            return list(self._violations)
        return [v for v in self._violations if v["type"] == violation_type]

    def get_blocked_count(self) -> int:
        now = time.time()
        return sum(1 for expires in self._blocked.values() if expires > now)

    def set_rate_limit(self, limit: int) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        self._rate_limit = limit

    def get_stats(self) -> Dict[str, Any]:
        return {"rate_limit": self._rate_limit, "total_violations": len(self._violations),
                "blocked_clients": self.get_blocked_count()}
