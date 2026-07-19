"""StartupManager — application startup and shutdown orchestration."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class StartupPhase(str, Enum):
    INIT = "init"; DEPS = "deps"; SERVICES = "services"; READY = "ready"


class StartupStep:
    __slots__ = ("name", "phase", "handler", "required", "status", "duration_ms")

    def __init__(self, name: str, phase: StartupPhase, handler: Callable,
                 required: bool = True) -> None:
        self.name = name
        self.phase = phase
        self.handler = handler
        self.required = required
        self.status = "pending"
        self.duration_ms: float = 0.0


class StartupManager:
    def __init__(self) -> None:
        self._steps: List[StartupStep] = []
        self._history: List[Dict[str, Any]] = []

    def add_step(self, name: str, phase: StartupPhase, handler: Callable,
                 required: bool = True) -> StartupStep:
        step = StartupStep(name, phase, handler, required)
        self._steps.append(step)
        return step

    def startup(self) -> Dict[str, Any]:
        results = []
        for step in sorted(self._steps, key=lambda s: s.phase.value):
            start = time.time()
            try:
                step.handler()
                step.status = "success"
            except Exception as exc:
                step.status = "failed" if step.required else "skipped"
                results.append({"step": step.name, "status": step.status, "error": str(exc)})
                if step.required:
                    return {"status": "failed", "failed_step": step.name, "results": results}
            step.duration_ms = (time.time() - start) * 1000
            results.append({"step": step.name, "status": step.status,
                           "duration_ms": round(step.duration_ms, 2)})
        self._history.extend(results)
        return {"status": "success", "results": results}

    def list_steps(self) -> List[Dict[str, Any]]:
        return [{"name": s.name, "phase": s.phase.value, "required": s.required,
                 "status": s.status} for s in self._steps]

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
