"""Recovery Manager — Orchestrate the full failure recovery pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List, Optional

from layers.layer07_publishing.modules.failure_recovery.failure_detector import (
    FailureDetector, FailureRecord,
)
from layers.layer07_publishing.modules.failure_recovery.error_classifier import (
    ErrorClassifier,
)
from layers.layer07_publishing.modules.failure_recovery.retry_strategy import (
    RetryStrategy,
)
from layers.layer07_publishing.modules.failure_recovery.circuit_breaker import (
    CircuitBreaker,
)
from layers.layer07_publishing.modules.failure_recovery.rollback_manager import (
    RollbackManager,
)
from layers.layer07_publishing.modules.failure_recovery.incident_logger import (
    IncidentLogger, IncidentEntry,
)
from layers.layer07_publishing.modules.failure_recovery.recovery_metrics import (
    RecoveryMetrics,
)
from layers.layer07_publishing.modules.failure_recovery.failure_memory import (
    FailureMemory,
)

_MANAGER_COUNTER = itertools.count(1)


class RecoveryResult:
    """Result of a recovery operation."""

    __slots__ = (
        "success", "recovered", "action", "attempts",
        "final_status", "incident_id", "duration_ms",
    )

    def __init__(self) -> None:
        self.success: bool = False
        self.recovered: bool = False
        self.action: str = "none"
        self.attempts: int = 0
        self.final_status: str = "failed"
        self.incident_id: str = ""
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "recovered": self.recovered,
            "action": self.action,
            "attempts": self.attempts,
            "final_status": self.final_status,
            "incident_id": self.incident_id,
            "duration_ms": round(self.duration_ms, 2),
        }


class RecoveryManager:
    """Orchestrate the full failure recovery pipeline.

    Flow: Detect → Classify → Recover → Retry/Rollback → Return result
    """

    def __init__(
        self,
        detector: Optional[FailureDetector] = None,
        classifier: Optional[ErrorClassifier] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        rollback_manager: Optional[RollbackManager] = None,
        incident_logger: Optional[IncidentLogger] = None,
        metrics: Optional[RecoveryMetrics] = None,
        failure_memory: Optional[FailureMemory] = None,
        retry_strategy: Optional[RetryStrategy] = None,
    ) -> None:
        self.detector = detector or FailureDetector()
        self.classifier = classifier or ErrorClassifier()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.rollback_manager = rollback_manager or RollbackManager()
        self.incident_logger = incident_logger or IncidentLogger()
        self.metrics = metrics or RecoveryMetrics()
        self.failure_memory = failure_memory or FailureMemory()
        self.retry_strategy = retry_strategy or RetryStrategy()
        self._events: List[Dict[str, Any]] = []
        self._recovery_count = 0

    def handle_failure(
        self,
        record: FailureRecord,
        publish_fn: Callable[[], bool],
        platform: str = "",
        request_id: str = "",
    ) -> RecoveryResult:
        start = time.time()
        result = RecoveryResult()
        circuit_key = f"{platform}_{record.error_type}"

        # Step 1: Check circuit breaker
        if not self.circuit_breaker.can_execute(circuit_key):
            result.action = "circuit_open"
            result.final_status = "blocked"
            result.incident_id = self._log_incident(record, "circuit_open")
            result.success = False
            result.recovered = False
            self._record_failure(False, start)
            return result

        # Step 2: Classify error
        classification = self.classifier.classify(record)

        # Step 3: Check failure memory for known patterns
        best_strategy = self.failure_memory.get_best_strategy(
            record.error_type, platform
        )

        # Step 4: Execute recovery
        if classification.retryable:
            recovery_result = self._execute_retry(publish_fn, record, platform)
            result.success = recovery_result["success"]
            result.recovered = recovery_result["recovered"]
            result.action = recovery_result["action"]
            result.attempts = recovery_result["attempts"]
        else:
            result.action = classification.suggested_action
            result.success = False
            result.recovered = False

        # Step 5: Record in circuit breaker + memory
        if result.success:
            self.circuit_breaker.record_success(circuit_key)
            self.failure_memory.observe(record, recovered=True)
        else:
            self.circuit_breaker.record_failure(circuit_key)
            self.failure_memory.observe(record, recovered=False)

        # Step 6: Incident logging
        incident = self._log_incident(record, result.action)
        result.incident_id = incident.incident_id

        # Step 7: Metrics
        elapsed = (time.time() - start) * 1000
        result.duration_ms = elapsed
        self.metrics.record_failure(result.recovered, elapsed)

        # Step 8: Event
        self._events.append({
            "event": "recovery_completed" if result.success else "recovery_failed",
            "incident_id": result.incident_id,
            "action": result.action,
            "attempts": result.attempts,
        })

        result.final_status = "published" if result.success else "failed"
        self._recovery_count += 1
        return result

    def handle_exception(
        self,
        exception: Exception,
        publish_fn: Callable[[], bool],
        platform: str = "",
        request_id: str = "",
    ) -> RecoveryResult:
        record = self.detector.detect_from_exception(
            exception, platform, request_id
        )
        return self.handle_failure(record, publish_fn, platform, request_id)

    def handle_response(
        self,
        response: Dict[str, Any],
        publish_fn: Callable[[], bool],
        platform: str = "",
        request_id: str = "",
    ) -> RecoveryResult:
        record = self.detector.detect_from_response(response, platform, request_id)
        if record is None:
            result = RecoveryResult()
            result.success = True
            result.final_status = "published"
            return result
        return self.handle_failure(record, publish_fn, platform, request_id)

    def _execute_retry(
        self,
        publish_fn: Callable[[], bool],
        record: FailureRecord,
        platform: str,
    ) -> Dict[str, Any]:
        attempt = 0
        while self.retry_strategy.should_retry(attempt):
            delay = self.retry_strategy.get_delay(attempt)
            time.sleep(min(delay / 10, 0.5))  # simulated delay in tests
            try:
                success = publish_fn()
                self.retry_strategy.record_attempt(attempt, success=success)
                self.metrics.record_retry()
                if success:
                    return {"success": True, "recovered": True, "action": "retry_success",
                            "attempts": attempt + 1}
            except Exception as e:
                self.retry_strategy.record_attempt(attempt, str(e))
                self.metrics.record_retry()
            attempt += 1
        return {"success": False, "recovered": False, "action": "retry_exhausted",
                "attempts": attempt}

    def _log_incident(self, record: FailureRecord, action: str) -> IncidentEntry:
        incident = self.incident_logger.log_incident(record)
        incident.recovery_action = action
        if action in ("retry_success", "recovered"):
            incident.mark_resolved()
        return incident

    def _record_failure(self, recovered: bool, start: float) -> None:
        self.metrics.record_failure(recovered, (time.time() - start) * 1000)

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def recovery_count(self) -> int:
        return self._recovery_count
