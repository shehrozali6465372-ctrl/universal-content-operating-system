"""recovery_testing.py — Recovery testing."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class RecoveryTest:
    """A recovery test result."""
    __slots__ = ("test_id", "plan_id", "success", "duration_ms",
                 "issues", "timestamp")
    _counter = 0

    def __init__(self, plan_id: int, success: bool, duration_ms: float = 0.0) -> None:
        RecoveryTest._counter += 1
        self.test_id: int = RecoveryTest._counter
        self.plan_id = plan_id
        self.success = success
        self.duration_ms = duration_ms
        self.issues: List[str] = []
        self.timestamp: float = time.time()


class RecoveryTestManager:
    """Manages recovery tests."""

    def __init__(self) -> None:
        self._tests: List[RecoveryTest] = []

    def run_test(self, plan_id: int, success: bool = True,
                 duration_ms: float = 0.0) -> RecoveryTest:
        test = RecoveryTest(plan_id, success, duration_ms)
        self._tests.append(test)
        return test

    def get_tests(self, plan_id: int = 0) -> List[RecoveryTest]:
        if plan_id:
            return [t for t in self._tests if t.plan_id == plan_id]
        return list(self._tests)

    def success_rate(self) -> float:
        if not self._tests:
            return 0.0
        return sum(1 for t in self._tests if t.success) / len(self._tests)

    def stats(self) -> Dict[str, Any]:
        return {"tests": len(self._tests), "success_rate": self.success_rate()}
