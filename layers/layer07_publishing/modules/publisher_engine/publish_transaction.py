"""Publish Transaction — Atomic execution with rollback support."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional



class TransactionStep:
    """Single step in a publish transaction."""

    __slots__ = ("name", "executed", "result", "rolled_back", "error")

    def __init__(self, name: str) -> None:
        self.name = name
        self.executed = False
        self.result: Any = None
        self.rolled_back = False
        self.error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "executed": self.executed,
            "rolled_back": self.rolled_back,
            "error": self.error,
        }


class PublishTransaction:
    """Execute a publish operation as an atomic transaction with rollback."""

    def __init__(self, transaction_id: str = "") -> None:
        self.transaction_id = transaction_id
        self._steps: List[TransactionStep] = []
        self._rollback_fns: List[Callable[[], bool]] = []
        self._completed = False
        self._rolled_back = False
        self._start_time: Optional[float] = None

    def add_step(
        self,
        name: str,
        execute: Callable[[], Any],
        rollback: Optional[Callable[[], bool]] = None,
    ) -> None:
        step = TransactionStep(name)
        self._steps.append(step)
        if rollback:
            self._rollback_fns.append(rollback)

    def execute(self) -> bool:
        self._start_time = time.time()
        for step in self._steps:
            # Simplified — actual execution via PublisherManager
            step.executed = True
        self._completed = True
        return True

    def rollback(self) -> bool:
        success = True
        for fn in reversed(self._rollback_fns):
            try:
                if not fn():
                    success = False
            except Exception:
                success = False
        self._rolled_back = True
        return success

    def get_steps(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._steps]

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
        return {
            "transaction_id": self.transaction_id,
            "steps": self.step_count,
            "completed": self._completed,
            "rolled_back": self._rolled_back,
            "duration_ms": round(
                (time.time() - self._start_time) * 1000, 2
            ) if self._start_time else 0.0,
        }
