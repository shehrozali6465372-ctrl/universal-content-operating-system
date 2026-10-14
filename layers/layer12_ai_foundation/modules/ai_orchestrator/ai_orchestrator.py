"""AIOrchestrator — main AI foundation orchestrator tying all modules together."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional

from .orchestrator_config import OrchestratorConfig
from .ai_pipeline import AIPipeline
from .ai_task_manager import AITaskManager
from .ai_router import AIRouter
from .ai_state_manager import AIStateManager
from .ai_metrics import AIMetrics
from .ai_events import AIEvents
from .ai_health import AIHealth
from .ai_cache import AICache
from .ai_scheduler import AIScheduler
from .ai_validator import AIValidator
from .ai_memory import AIMemory
from .ai_monitor import AIMonitor
from .ai_report import AIReportGenerator


class AIOrchestrator:
    """Main AI foundation orchestrator — ties all 10 modules together."""

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

    def start(self) -> bool:
        self._is_running = True
        self.state.transition("running")
        self.events.publish("orchestrator_started")
        return True

    def stop(self) -> bool:
        self._is_running = False
        self.state.transition("idle")
        self.events.publish("orchestrator_stopped")
        return True

    def link_module(self, name: str, module: Any) -> None:
        self._linked_modules[name] = module
        self.health.check(name, True)

    def process(self, task: str, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start = time.time()
        # Validate
        validation = self.validator.validate_task(task, input_data)
        if not validation["valid"]:
            return {"success": False, "error": validation["issues"]}

        # Route
        target = self.router.route(task)
        component = self._linked_modules.get(target)

        # Execute only a registered component with an explicit supported interface.
        if component is None:
            result = {
                "success": False,
                "status": "blocked",
                "error": "No execution component is registered for the routed task",
                "component": target,
                "task": task,
            }
        else:
            try:
                if callable(getattr(component, "evaluate", None)):
                    result = component.evaluate(str(input_data))
                elif callable(getattr(component, "check", None)):
                    result = component.check(str(input_data))
                else:
                    result = {
                        "success": False,
                        "status": "blocked",
                        "error": "Registered component exposes no supported execution method",
                        "component": target,
                        "task": task,
                    }
                if not isinstance(result, dict):
                    result = {
                        "success": False,
                        "status": "failed",
                        "error": "Execution component returned a non-dictionary result",
                        "component": target,
                        "task": task,
                    }
            except Exception as exc:
                result = {
                    "success": False,
                    "status": "failed",
                    "error": f"Execution component failed: {type(exc).__name__}",
                    "component": target,
                    "task": task,
                }
                self.monitor.alert("error", f"Task failed: {task}")

        elapsed = (time.time() - start) * 1000
        success = result.get("success") is True or (
            "error" not in result and result.get("status") not in {"blocked", "failed"}
        )
        result.setdefault("success", success)
        self.metrics.record_task(target, success, elapsed)
        self.memory.store(task, "success" if success else "failed")
        self.events.publish("task_completed", {"task": task, "success": success})
        return result

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._is_running,
            "state": self.state.get_state(),
            "metrics": self.metrics.to_dict(),
            "linked_modules": list(self._linked_modules.keys()),
            "health": self.health.overall_health(),
        }

    def generate_report(self) -> Dict[str, Any]:
        return self.report_gen.generate(self.metrics.to_dict(), self.health.overall_health())

    def get_health(self) -> Dict[str, Any]:
        return self.health.overall_health()
