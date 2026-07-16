"""Error Classifier — Classify errors by retryability and recovery path."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer07_publishing.modules.failure_recovery.failure_detector import FailureRecord


RETRYABLE = "retryable"
PERMANENT = "permanent"
USER_ACTION = "user_action"
PLATFORM_SPECIFIC = "platform_specific"


class ErrorClassification:
    """Classification result for a failure."""

    __slots__ = ("category", "retryable", "suggested_action", "confidence", "details")

    def __init__(self, category: str = "unknown") -> None:
        self.category = category
        self.retryable: bool = False
        self.suggested_action: str = ""
        self.confidence: float = 0.8
        self.details: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "retryable": self.retryable,
            "suggested_action": self.suggested_action,
            "confidence": self.confidence,
        }


class ErrorClassifier:
    """Classify failures into categories for recovery routing."""

    RETRYABLE_TYPES = {"network", "rate_limit", "api"}
    PERMANENT_TYPES = {"auth", "content"}
    PLATFORM_TYPES = {"platform"}

    def __init__(self) -> None:
        self._classification_count = 0

    def classify(self, record: FailureRecord) -> ErrorClassification:
        classification = ErrorClassification()
        etype = record.error_type

        if etype in self.RETRYABLE_TYPES:
            classification.category = RETRYABLE
            classification.retryable = True
            classification.suggested_action = self._get_retry_action(record)
        elif etype in self.PERMANENT_TYPES:
            classification.category = PERMANENT
            classification.retryable = False
            classification.suggested_action = self._get_permanent_action(record)
        elif etype in self.PLATFORM_TYPES:
            classification.category = PLATFORM_SPECIFIC
            classification.retryable = False
            classification.suggested_action = self._get_platform_action(record)
        else:
            classification.category = "unknown"
            classification.retryable = False
            classification.suggested_action = "manual_review"

        classification.confidence = self._confidence(record, classification)
        classification.details = {
            "error_type": etype,
            "severity": record.severity,
            "platform": record.platform,
        }
        self._classification_count += 1
        return classification

    def classify_batch(self, records: List[FailureRecord]) -> List[ErrorClassification]:
        return [self.classify(r) for r in records]

    def is_retryable(self, record: FailureRecord) -> bool:
        return record.error_type in self.RETRYABLE_TYPES

    def get_recovery_path(self, record: FailureRecord) -> str:
        cls = self.classify(record)
        return cls.suggested_action

    def _get_retry_action(self, record: FailureRecord) -> str:
        if record.error_type == "rate_limit":
            return "wait_and_retry"
        if record.error_type == "network":
            return "immediate_retry"
        return "exponential_backoff"

    def _get_permanent_action(self, record: FailureRecord) -> str:
        if record.error_type == "auth":
            return "refresh_token"
        return "revise_content"

    def _get_platform_action(self, record: FailureRecord) -> str:
        return "check_platform_status"

    def _confidence(self, record: FailureRecord, cls: ErrorClassification) -> float:
        base = 0.8
        if record.error_type in ("rate_limit", "auth"):
            base = 0.95
        elif record.error_type == "unknown":
            base = 0.5
        return base

    @property
    def classification_count(self) -> int:
        return self._classification_count
