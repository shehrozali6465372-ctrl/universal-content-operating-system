"""Circuit Breaker — Prevent API flooding with open/half-open/closed states."""
from __future__ import annotations
import time
from typing import Any, Dict, List

STATE_CLOSED = "closed"
STATE_OPEN = "open"
STATE_HALF_OPEN = "half_open"


class CircuitState:
    """Current state of a circuit breaker."""

    __slots__ = ("state", "failure_count", "success_count",
                 "last_failure_time", "last_state_change")

    def __init__(self) -> None:
        self.state: str = STATE_CLOSED
        self.failure_count: int = 0
        self.success_count: int = 0
        self.last_failure_time: float = 0.0
        self.last_state_change: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
        }


class CircuitBreaker:
    """Circuit breaker to prevent API flooding.

    States:
    - closed: Normal operation, requests pass through
    - open: Too many failures, requests are blocked
    - half_open: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self._circuits: Dict[str, CircuitState] = {}

    def _get_state(self, key: str) -> CircuitState:
        if key not in self._circuits:
            self._circuits[key] = CircuitState()
        return self._circuits[key]

    def can_execute(self, key: str) -> bool:
        state = self._get_state(key)
        if state.state == STATE_CLOSED:
            return True
        if state.state == STATE_OPEN:
            if time.time() - state.last_failure_time >= self.recovery_timeout:
                state.state = STATE_HALF_OPEN
                state.last_state_change = time.time()
                return True
            return False
        if state.state == STATE_HALF_OPEN:
            return True
        return False

    def record_success(self, key: str) -> None:
        state = self._get_state(key)
        state.success_count += 1
        if state.state == STATE_HALF_OPEN:
            if state.success_count >= self.success_threshold:
                state.state = STATE_CLOSED
                state.failure_count = 0
                state.success_count = 0
                state.last_state_change = time.time()
        elif state.state == STATE_CLOSED:
            state.success_count += 1

    def record_failure(self, key: str) -> None:
        state = self._get_state(key)
        state.failure_count += 1
        state.last_failure_time = time.time()
        if state.state == STATE_HALF_OPEN:
            state.state = STATE_OPEN
            state.last_state_change = time.time()
        elif state.state == STATE_CLOSED:
            if state.failure_count >= self.failure_threshold:
                state.state = STATE_OPEN
                state.last_state_change = time.time()

    def get_state(self, key: str) -> str:
        return self._get_state(key).state

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        return {k: v.to_dict() for k, v in self._circuits.items()}

    def reset(self, key: str) -> None:
        if key in self._circuits:
            self._circuits[key] = CircuitState()

    def reset_all(self) -> None:
        self._circuits.clear()

    @property
    def open_circuits(self) -> List[str]:
        return [k for k, v in self._circuits.items() if v.state == STATE_OPEN]

    @property
    def circuit_count(self) -> int:
        return len(self._circuits)
