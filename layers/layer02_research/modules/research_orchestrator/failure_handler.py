"""
Failure Handler
Layer 2: Research Engine — Module 10

Handles module failures:
- Classify failure types
- Determine recovery strategy
- Track failure patterns
- Fallback execution
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from layers.layer02_research.modules.research_orchestrator.retry_coordinator import RetryCoordinator, RetryPolicy


FAILURE_TYPES = {
    "api_error": {"retryable": True, "strategy": "retry"},
    "timeout": {"retryable": True, "strategy": "retry"},
    "data_error": {"retryable": False, "strategy": "skip"},
    "dependency_error": {"retryable": False, "strategy": "fail"},
    "resource_error": {"retryable": True, "strategy": "retry_with_backoff"},
    "unknown": {"retryable": True, "strategy": "retry"},
}


class FailureRecord:
    """Record of a module failure."""

    __slots__ = ("module", "error_type", "error_message", "timestamp", "recovery_action")

    def __init__(self, module: str, error_type: str, error_message: str, recovery_action: str = ""):
        self.module = module
        self.error_type = error_type
        self.error_message = error_message
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.recovery_action = recovery_action

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "recovery_action": self.recovery_action,
        }


class FailureHandler:
    """Classifies failures and determines recovery strategies."""

    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_coordinator = RetryCoordinator(retry_policy)
        self._failure_log: List[FailureRecord] = []
        self._failure_counts: Dict[str, int] = {}

    def classify_error(self, error: Exception) -> str:
        """Classify an error into a failure type."""
        error_msg = str(error).lower()
        error_type_name = type(error).__name__.lower()

        if "timeout" in error_msg or "timed out" in error_msg:
            return "timeout"
        elif "api" in error_msg or "http" in error_msg or "connection" in error_msg:
            return "api_error"
        elif "key" in error_msg or "value" in error_msg or "type" in error_msg or error_type_name in ("valueerror", "typeerror", "keyerror"):
            return "data_error"
        elif "import" in error_msg or "module" in error_type_name:
            return "dependency_error"
        elif "memory" in error_msg or "resource" in error_msg:
            return "resource_error"
        return "unknown"

    def get_strategy(self, error_type: str) -> str:
        """Get the recovery strategy for an error type."""
        return FAILURE_TYPES.get(error_type, FAILURE_TYPES["unknown"])["strategy"]

    def is_retryable(self, error_type: str) -> bool:
        """Check if an error type is retryable."""
        return FAILURE_TYPES.get(error_type, FAILURE_TYPES["unknown"])["retryable"]

    def handle_failure(
        self,
        module: str,
        error: Exception,
        fallback_func: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Handle a module failure. Returns recovery decision."""
        error_type = self.classify_error(error)
        strategy = self.get_strategy(error_type)
        retryable = self.is_retryable(error_type)

        record = FailureRecord(module, error_type, str(error), strategy)
        self._failure_log.append(record)
        self._failure_counts[module] = self._failure_counts.get(module, 0) + 1

        result: Dict[str, Any] = {
            "module": module,
            "error_type": error_type,
            "strategy": strategy,
            "retryable": retryable,
            "attempt": self._failure_counts[module],
        }

        if retryable and self.retry_coordinator.should_retry(module):
            result["action"] = "retry"
            result["delay"] = self.retry_coordinator.get_delay(module)
            self.retry_coordinator.record_attempt(module, str(error))
        elif fallback_func is not None:
            result["action"] = "fallback"
            try:
                fallback_result = fallback_func()
                result["fallback_success"] = True
                result["fallback_result"] = fallback_result
            except Exception as fb_exc:
                result["fallback_success"] = False
                result["fallback_error"] = str(fb_exc)
        else:
            result["action"] = "skip"

        return result

    def get_failure_log(self, module: Optional[str] = None) -> List[FailureRecord]:
        """Get failure log, optionally filtered by module."""
        if module:
            return [r for r in self._failure_log if r.module == module]
        return list(self._failure_log)

    def get_failure_counts(self) -> Dict[str, int]:
        """Get failure counts per module."""
        return dict(self._failure_counts)

    def get_most_failed_module(self) -> Optional[str]:
        """Get the module with the most failures."""
        if not self._failure_counts:
            return None
        return max(self._failure_counts, key=self._failure_counts.get)

    def reset(self):
        """Clear all failure tracking."""
        self._failure_log.clear()
        self._failure_counts.clear()
        self.retry_coordinator.reset_all()
