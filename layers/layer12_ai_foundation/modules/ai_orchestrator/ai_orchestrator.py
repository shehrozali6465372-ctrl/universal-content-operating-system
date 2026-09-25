"""AIOrchestrator — main AI foundation orchestrator."""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

from .ai_cache import AICache
from .ai_events import AIEvents
from .ai_health import AIHealth
from .ai_memory import AIMemory
from .ai_metrics import AIMetrics
from .ai_monitor import AIMonitor
from .ai_pipeline import AIPipeline
from .ai_report import AIReportGenerator
from .ai_router import AIRouter
from .ai_scheduler import AIScheduler
from .ai_state_manager import AIStateManager
from .ai_task_manager import AITaskManager
from .ai_validator import AIValidator
from .orchestrator_config import OrchestratorConfig

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """Main AI foundation orchestrator with fail-closed production routing."""

    def __init__(self, config: Optional[OrchestratorConfig] = None) -> None:
        self.config = config or OrchestratorConfig()
        self.pipeline = AIPipeline()
        self.task_manager = AITaskManager()
        self.router = AIRouter()
        self.state = AIStateManager()
        self.metrics = AIMetrics()
        self.events = AIEvents()
        self.health = AIHealth()
        self.cache = AICache()
        self.scheduler = AIScheduler()
        self.validator = AIValidator()
        self.memory = AIMemory()
        self.monitor = AIMonitor()
        self.report_gen = AIReportGenerator()
        self._is_running = False
        self._linked_modules: Dict[str, Any] = {}

    @staticmethod
    def _is_production() -> bool:
        return os.getenv("UCOS_ENV", "").strip().lower() == "production"

    def start(self) -> bool:
        if self._is_running:
            return True
        self._is_running = True
        self.state.transition("running")
        self.events.publish("orchestrator_started")
        return True

    def stop(self) -> bool:
        if not self._is_running:
            return True
        self._is_running = False
        self.state.transition("idle")
        self.events.publish("orchestrator_stopped")
        return True

    def link_module(self, name: str, module: Any) -> None:
        name = name.strip()
        if not name:
            raise ValueError("module name must not be empty")
        if module is None:
            raise ValueError("module must not be None")
        if not callable(getattr(module, "evaluate", None)) and not callable(getattr(module, "check", None)):
            raise TypeError(f"module '{name}' must expose callable evaluate() or check()")
        self._linked_modules[name] = module
        self.health.check(name, True)

    def process(self, task: str, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start = time.time()
        if self._is_production() and not self._is_running:
            return {"success": False, "error": "AI orchestrator is not running",
                    "error_code": "ORCHESTRATOR_NOT_RUNNING"}
        validation = self.validator.validate_task(task, input_data)
        if not validation["valid"]:
            return {"success": False, "error": validation["issues"],
                    "error_code": "VALIDATION_FAILED"}
        target = self.router.route(task)
        component = self._linked_modules.get(target)
        try:
            if component is None:
                if self._is_production():
                    raise RuntimeError(f"No linked production component for route '{target}'")
                result = {"component": target, "task": task, "processed": True, "simulated": True}
            elif hasattr(component, "evaluate"):
                result = component.evaluate(str(input_data))
            elif hasattr(component, "check"):
                result = component.check(str(input_data))
            else:
                raise TypeError(f"Linked component '{target}' has no supported execution method")
            if not isinstance(result, dict):
                raise TypeError(f"Linked component '{target}' returned non-dict result")
        except Exception as exc:
            logger.exception("AI orchestration task failed: task=%s", task)
            self.monitor.alert("error", f"Task failed: {task}")
            result = {"success": False, "error": str(exc), "error_code": "TASK_EXECUTION_FAILED"}
        elapsed = (time.time() - start) * 1000
        success = bool(result.get("success", "error" not in result))
        self.metrics.record_task(target, success, elapsed)
        self.memory.store(task, "success" if success else "failed")
        self.events.publish("task_completed", {"task": task, "success": success})
        return result

    def get_status(self) -> Dict[str, Any]:
        return {"running": self._is_running, "state": self.state.get_state(),
                "metrics": self.metrics.to_dict(),
                "linked_modules": list(self._linked_modules),
                "health": self.health.overall_health()}

    def generate_report(self) -> Dict[str, Any]:
        return self.report_gen.generate(self.metrics.to_dict(), self.health.overall_health())

    def get_health(self) -> Dict[str, Any]:
        return self.health.overall_health()
