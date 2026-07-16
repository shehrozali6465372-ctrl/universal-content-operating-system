"""Failure Detector — Detect and categorize publishing failures."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, Optional

_DETECT_COUNTER = itertools.count(1)

ERROR_TYPES = ("network", "api", "auth", "rate_limit", "media", "content", "platform", "unknown")

SEVERITY_LEVELS = ("low", "medium", "high", "critical")


class FailureRecord:
    """Record of a detected failure."""

    __slots__ = (
        "failure_id", "error_type", "severity", "message",
        "platform", "request_id", "post_id", "timestamp",
        "context", "stack_trace",
    )

    def __init__(self, error_type: str = "unknown", message: str = "", platform: str = "") -> None:
        self.failure_id: str = f"fail_{next(_DETECT_COUNTER)}"
        self.error_type = error_type if error_type in ERROR_TYPES else "unknown"
        self.severity: str = "medium"
        self.message = message[:500]
        self.platform = platform
        self.request_id: str = ""
        self.post_id: str = ""
        self.timestamp: float = time.time()
        self.context: Dict[str, Any] = {}
        self.stack_trace: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "error_type": self.error_type,
            "severity": self.severity,
            "message": self.message,
            "platform": self.platform,
            "request_id": self.request_id,
            "post_id": self.post_id,
            "timestamp": self.timestamp,
        }


class FailureDetector:
    """Detect and categorize failures from exceptions and API responses."""

    NETWORK_PATTERNS = ("timeout", "connection", "network", "unreachable", "dns", "ssl")
    API_PATTERNS = ("api error", "server error", "500", "502", "503", "internal")
    AUTH_PATTERNS = ("unauthorized", "invalid token", "expired", "access denied", "401", "403")
    RATE_PATTERNS = ("rate limit", "too many requests", "throttled", "429")
    MEDIA_PATTERNS = ("upload failed", "file too large", "invalid format", "image error")
    CONTENT_PATTERNS = ("spam", "violates policy", "invalid content", "blocked")

    def __init__(self) -> None:
        self._detection_count = 0

    def detect_from_exception(
        self,
        exception: Exception,
        platform: str = "",
        request_id: str = "",
        post_id: str = "",
    ) -> FailureRecord:
        msg = str(exception).lower()
        error_type = self._classify_message(msg)
        severity = self._assess_severity(error_type, msg)
        record = FailureRecord(error_type, str(exception))
        record.severity = severity
        record.platform = platform
        record.request_id = request_id
        record.post_id = post_id
        record.stack_trace = self._get_trace(exception)
        self._detection_count += 1
        return record

    def detect_from_response(
        self,
        response: Dict[str, Any],
        platform: str = "",
        request_id: str = "",
    ) -> Optional[FailureRecord]:
        error = response.get("error", "")
        if isinstance(error, dict):
            error = error.get("message", "")
        if not error:
            return None
        msg = str(error).lower()
        error_type = self._classify_message(msg)
        severity = self._assess_severity(error_type, msg)
        record = FailureRecord(error_type, str(error))
        record.severity = severity
        record.platform = platform
        record.request_id = request_id
        self._detection_count += 1
        return record

    def detect_from_status_code(
        self,
        status_code: int,
        platform: str = "",
        request_id: str = "",
    ) -> FailureRecord:
        if status_code == 429:
            error_type, severity = "rate_limit", "high"
            msg = f"Rate limited (HTTP {status_code})"
        elif status_code in (401, 403):
            error_type, severity = "auth", "high"
            msg = f"Auth error (HTTP {status_code})"
        elif status_code >= 500:
            error_type, severity = "api", "high"
            msg = f"Server error (HTTP {status_code})"
        elif status_code == 404:
            error_type, severity = "platform", "medium"
            msg = f"Not found (HTTP {status_code})"
        else:
            error_type, severity = "api", "medium"
            msg = f"HTTP error {status_code}"
        record = FailureRecord(error_type, msg)
        record.severity = severity
        record.platform = platform
        record.request_id = request_id
        self._detection_count += 1
        return record

    def _classify_message(self, msg: str) -> str:
        for pattern in self.NETWORK_PATTERNS:
            if pattern in msg:
                return "network"
        for pattern in self.RATE_PATTERNS:
            if pattern in msg:
                return "rate_limit"
        for pattern in self.AUTH_PATTERNS:
            if pattern in msg:
                return "auth"
        for pattern in self.MEDIA_PATTERNS:
            if pattern in msg:
                return "media"
        for pattern in self.CONTENT_PATTERNS:
            if pattern in msg:
                return "content"
        for pattern in self.API_PATTERNS:
            if pattern in msg:
                return "api"
        return "unknown"

    def _assess_severity(self, error_type: str, msg: str) -> str:
        if error_type in ("auth", "content"):
            return "high"
        if error_type == "rate_limit":
            return "medium"
        if error_type == "network":
            return "medium"
        if error_type == "media":
            return "medium"
        return "low"

    def _get_trace(self, exc: Exception) -> str:
        import traceback
        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[:1000]

    @property
    def detection_count(self) -> int:
        return self._detection_count
