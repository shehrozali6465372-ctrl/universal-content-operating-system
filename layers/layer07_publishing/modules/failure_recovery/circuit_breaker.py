"""Circuit Breaker — thread-safe closed/open/half-open protection."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List

STATE_CLOSED = "closed"
STATE_OPEN = "open"
STATE_HALF_OPEN = "half_open"


class CircuitState:
    """Current state of a circuit breaker."""

    __slots__ = ("state", "failure_count", "success_count",
                 "last_failure_time", "last_state_change", "probe_in_flight")

    def __init__(self) -> None:
        self.state = STATE_CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.last_state_change = time.monotonic()
        self.probe_in_flight = False

    def to_dict(self) -> Dict[str, Any]:
        return {"state": self.state, "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time,
                "last_state_change": self.last_state_change,
                "probe_in_flight": self.probe_in_flight}


class CircuitBreaker:
    """Prevent API flooding and permit only one half-open probe."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0,
                 success_threshold: int = 2) -> None:
        if failure_threshold < 1 or recovery_timeout < 0 or success_threshold < 1:
            raise ValueError("Circuit breaker thresholds must be positive")
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self._circuits: Dict[str, CircuitState] = {}
        self._lock = threading.RLock()

    def _get_state(self, key: str) -> CircuitState:
        if not key:
            raise ValueError("Circuit key is required")
        state = self._circuits.get(key)
        if state is None:
            state = CircuitState()
            self._circuits[key] = state
        return state

    def can_execute(self, key: str) -> bool:
        with self._lock:
            state = self._get_state(key)
            if state.state == STATE_CLOSED:
                return True
            if state.state == STATE_OPEN:
                if time.monotonic() - state.last_failure_time < self.recovery_timeout:
                    return False
                state.state = STATE_HALF_OPEN
                state.success_count = 0
                state.probe_in_flight = True
                state.last_state_change = time.monotonic()
                return True
            if state.state == STATE_HALF_OPEN and not state.probe_in_flight:
                state.probe_in_flight = True
                return True
            return False

    def record_success(self, key: str) -> None:
        with self._lock:
            state = self._get_state(key)
            if state.state == STATE_HALF_OPEN:
                state.probe_in_flight = False
                state.success_count += 1
                if state.success_count >= self.success_threshold:
                    state.state = STATE_CLOSED
                    state.failure_count = 0
                    state.success_count = 0
                    state.last_state_change = time.monotonic()
            elif state.state == STATE_CLOSED:
                state.failure_count = 0

    def record_failure(self, key: str) -> None:
        with self._lock:
            state = self._get_state(key)
            state.failure_count += 1
            state.last_failure_time = time.monotonic()
            state.probe_in_flight = False
            if state.state == STATE_HALF_OPEN:
                state.state = STATE_OPEN
                state.success_count = 0
                state.last_state_change = time.monotonic()
            elif state.state == STATE_CLOSED and state.failure_count >= self.failure_threshold:
                state.state = STATE_OPEN
                state.last_state_change = time.monotonic()

    def get_state(self, key: str) -> str:
        with self._lock:
            return self._get_state(key).state

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {key: state.to_dict() for key, state in self._circuits.items()}

    def reset(self, key: str) -> None:
        with self._lock:
            self._circuits.pop(key, None)

    def reset_all(self) -> None:
        with self._lock:
            self._circuits.clear()

    @property
    def open_circuits(self) -> List[str]:
        with self._lock:
            return [key for key, state in self._circuits.items() if state.state == STATE_OPEN]

    @property
    def circuit_count(self) -> int:
        with self._lock:
            return len(self._circuits)
