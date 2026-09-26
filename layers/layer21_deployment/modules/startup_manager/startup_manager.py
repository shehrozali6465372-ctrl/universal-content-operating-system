"""Deterministic startup/shutdown orchestration with phase ordering and failure isolation."""
from __future__ import annotations
import time
from enum import IntEnum
from typing import Any, Callable, Dict, List

class StartupPhase(IntEnum):
    INIT = 10
    DEPS = 20
    SERVICES = 30
    READY = 40

class StartupStep:
    __slots__ = ("name", "phase", "handler", "required", "status", "duration_ms")
    def __init__(self, name: str, phase: StartupPhase, handler: Callable[[], Any], required: bool = True) -> None:
        if not name or not callable(handler):
            raise ValueError("Startup step requires a name and callable handler")
        self.name, self.phase, self.handler, self.required = name, phase, handler, required
        self.status, self.duration_ms = "pending", 0.0

class StartupManager:
    def __init__(self) -> None:
        self._steps: List[StartupStep] = []
        self._history: List[Dict[str, Any]] = []
    def add_step(self, name: str, phase: StartupPhase, handler: Callable[[], Any], required: bool = True) -> StartupStep:
        if any(step.name == name for step in self._steps):
            raise ValueError(f"Duplicate startup step: {name}")
        step = StartupStep(name, phase, handler, required)
        self._steps.append(step)
        return step
    def startup(self) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        for step in sorted(self._steps, key=lambda item: (item.phase, item.name)):
            started = time.monotonic()
            try:
                step.handler()
            except Exception as exc:
                step.status = "failed"
                result = {"step": step.name, "status": "failed", "error": str(exc),
                          "duration_ms": round((time.monotonic() - started) * 1000, 2)}
                results.append(result)
                self._history.append(result)
                if step.required:
                    return {"status": "failed", "failed_step": step.name, "results": results}
                continue
            step.status = "success"
            result = {"step": step.name, "status": "success",
                      "duration_ms": round((time.monotonic() - started) * 1000, 2)}
            results.append(result)
            self._history.append(result)
        return {"status": "success", "results": results}
    def reset(self) -> None:
        for step in self._steps:
            step.status = "pending"
    def list_steps(self) -> List[Dict[str, Any]]:
        return [{"name": step.name, "phase": step.phase.name, "required": step.required, "status": step.status}
                for step in self._steps]
    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
