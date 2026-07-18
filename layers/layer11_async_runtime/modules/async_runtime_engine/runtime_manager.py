"""RuntimeManager — Manage runtime lifecycle."""
from __future__ import annotations
from typing import Any, Dict, Optional

from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_config import RuntimeConfig
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_state import RuntimeState
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_metrics import RuntimeMetrics
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_events import RuntimeEvents
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_health import RuntimeHealth
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_memory import RuntimeMemory
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_profiler import RuntimeProfiler
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_registry import RuntimeRegistry
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_report import RuntimeReportGenerator
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_validator import RuntimeValidator
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_monitor import RuntimeMonitor


class RuntimeManager:
    """Main runtime lifecycle manager — start, stop, pause, monitor."""

    def __init__(self, config: Optional[RuntimeConfig] = None) -> None:
        self.config = config or RuntimeConfig()
        self.state = RuntimeState()
        self.metrics = RuntimeMetrics()
        self.events = RuntimeEvents()
        self.health = RuntimeHealth()
        self.memory = RuntimeMemory()
        self.profiler = RuntimeProfiler()
        self.registry = RuntimeRegistry()
        self.report_generator = RuntimeReportGenerator()
        self.validator = RuntimeValidator()
        self.monitor = RuntimeMonitor()

    def start(self) -> bool:
        if not self.state.transition(RuntimeState.STARTING):
            return False
        self.events.publish("runtime_starting", "manager")
        self.metrics.increment("start_count")
        self.state.transition(RuntimeState.RUNNING)
        self.events.publish("runtime_started", "manager")
        self.memory.save_checkpoint(RuntimeState.RUNNING)
        return True

    def stop(self) -> bool:
        if not self.state.transition(RuntimeState.STOPPING):
            return False
        self.events.publish("runtime_stopping", "manager")
        self.state.transition(RuntimeState.STOPPED)
        self.events.publish("runtime_stopped", "manager")
        self.memory.save_checkpoint(RuntimeState.STOPPED)
        return True

    def pause(self) -> bool:
        if self.state.transition(RuntimeState.PAUSED):
            self.events.publish("runtime_paused", "manager")
            return True
        return False

    def resume(self) -> bool:
        if self.state.transition(RuntimeState.RUNNING):
            self.events.publish("runtime_resumed", "manager")
            return True
        return False

    def restart(self) -> bool:
        self.stop()
        return self.start()

    def status(self) -> Dict[str, Any]:
        return {"state": self.state.to_dict(), "metrics": self.metrics.to_dict(),
                "health": self.health.get_stats(), "registry": self.registry.get_stats()}

    def health_check(self) -> Dict[str, Any]:
        results = self.health.run_checks()
        return {"healthy": self.health.is_healthy(),
                "checks": [r.to_dict() for r in results]}

    def generate_report(self, report_type: str = "status") -> Dict[str, Any]:
        report = self.report_generator.generate(report_type, self.status())
        return report.to_dict()

    def get_full_status(self) -> Dict[str, Any]:
        return {"state": self.state.current, "metrics": self.metrics.to_dict(),
                "health": self.health.is_healthy(),
                "registry_count": len(self.registry.get_all()),
                "memory_checkpoints": len(self.memory.get_all()),
                "events": self.events.get_stats()}
