"""Publish Transaction — executable steps with compensating rollback support."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional


class TransactionStep:
    """Single executable step in a publish transaction."""

    __slots__ = ("name", "execute_fn", "rollback_fn", "executed", "result", "rolled_back", "error")

    def __init__(self, name: str, execute_fn: Callable[[], Any],
                 rollback_fn: Optional[Callable[[], bool]] = None) -> None:
        self.name = name
        self.execute_fn = execute_fn
        self.rollback_fn = rollback_fn
        self.executed = False
        self.result: Any = None
        self.rolled_back = False
        self.error = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "executed": self.executed,
                "rolled_back": self.rolled_back, "error": self.error}


class PublishTransaction:
    """Execute publish steps and compensate only completed steps."""

    def __init__(self, transaction_id: str = "") -> None:
        self.transaction_id = transaction_id
        self._steps: List[TransactionStep] = []
        self._completed = False
        self._rolled_back = False
        self._start_time: Optional[float] = None

    def add_step(self, name: str, execute: Callable[[], Any],
                 rollback: Optional[Callable[[], bool]] = None) -> None:
        if self._start_time is not None:
            raise RuntimeError("Cannot add steps after transaction execution has started")
        self._steps.append(TransactionStep(name, execute, rollback))

    def execute(self) -> bool:
        if self._start_time is not None:
            raise RuntimeError("Transaction can only be executed once")
        if self._rolled_back:
            raise RuntimeError("Rolled-back transaction cannot be executed")
        self._start_time = time.monotonic()
        for step in self._steps:
            try:
                step.result = step.execute_fn()
                if step.result is False:
                    step.error = "Step returned False"
                    self.rollback()
                    return False
                step.executed = True
            except Exception as exc:
                step.error = str(exc)[:500]
                self.rollback()
                return False
        self._completed = True
        return True

    def rollback(self) -> bool:
        if self._rolled_back:
            return all(not step.executed or step.rollback_fn is None or step.rolled_back
                        for step in self._steps)
        success = True
        for step in reversed(self._steps):
            if not step.executed or step.rollback_fn is None:
                continue
            try:
                if step.rollback_fn():
                    step.rolled_back = True
                else:
                    success = False
                    step.error = step.error or "Rollback returned False"
            except Exception as exc:
                success = False
                step.error = str(exc)[:500]
        self._rolled_back = True
        self._completed = False
        return success

    def get_steps(self) -> List[Dict[str, Any]]:
        return [step.to_dict() for step in self._steps]

    @property
    def is_completed(self) -> bool:
        return self._completed

    @property
    def is_rolled_back(self) -> bool:
        return self._rolled_back

    @property
    def step_count(self) -> int:
        return len(self._steps)

    def to_dict(self) -> Dict[str, Any]:
        duration = ((time.monotonic() - self._start_time) * 1000
                    if self._start_time is not None else 0.0)
        return {"transaction_id": self.transaction_id, "steps": self.step_count,
                "completed": self._completed, "rolled_back": self._rolled_back,
                "duration_ms": round(duration, 2)}
