"""SecurityEngine — Rate limits, abuse detection, spam, injection protection."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class SecurityEngine:
    """Protect system from rate limit abuse, spam, injection, and prompt attacks."""

    def __init__(self, rate_limit: int = 60, window_seconds: int = 60) -> None:
        self._rate_limit = rate_limit
        self._window_seconds = window_seconds
        self._request_log: Dict[str, List[float]] = {}
        self._blocked: Dict[str, float] = {}
        self._violations: List[Dict[str, Any]] = []
        self._blocked_patterns: List[str] = [
            "ignore previous instructions",
            "ignore all previous",
            "you are now",
            "forget everything",
            "system prompt",
        ]

    def check_rate_limit(self, client_id: str) -> bool:
        now = time.time()
        requests = self._request_log.get(client_id, [])
        requests = [r for r in requests if now - r < self._window_seconds]
        self._request_log[client_id] = requests
        if len(requests) >= self._rate_limit:
            self._record_violation(client_id, "rate_limit_exceeded")
            return False
        requests.append(now)
        return True

    def is_blocked(self, client_id: str) -> bool:
        if client_id in self._blocked:
            if time.time() < self._blocked[client_id]:
                return True
            del self._blocked[client_id]
        return False

    def block(self, client_id: str, duration_seconds: int = 300) -> None:
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
        words = text.split()
        if len(words) > 500:
            self._record_violation("input", "potential_spam")
            return True
        if len(set(w.lower() for w in words)) < len(words) * 0.2 and len(words) > 20:
            self._record_violation("input", "repetitive_content")
            return True
        return False

    def _record_violation(self, source: str, violation_type: str) -> None:
        self._violations.append({"source": source, "type": violation_type,
                                  "timestamp": time.time()})

    def get_violations(self, violation_type: str = "") -> List[Dict[str, Any]]:
        violations = self._violations
        if violation_type:
            violations = [v for v in violations if v["type"] == violation_type]
        return violations

    def get_blocked_count(self) -> int:
        now = time.time()
        return sum(1 for exp in self._blocked.values() if exp > now)

    def set_rate_limit(self, limit: int) -> None:
        self._rate_limit = limit

    def get_stats(self) -> Dict[str, Any]:
        return {"rate_limit": self._rate_limit,
                "total_violations": len(self._violations),
                "blocked_clients": self.get_blocked_count()}
