"""UniversalOSOrchestrator — explicit stage execution without fabricated success."""
from __future__ import annotations
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from layers.layer10_monetization.modules.universal_os.universal_ai_os import UniversalAIOS
from layers.layer10_monetization.modules.universal_os.system_kernel import SystemKernel
from layers.layer10_monetization.modules.universal_os.global_context_manager import GlobalContextManager
from layers.layer10_monetization.modules.universal_os.global_memory import GlobalMemory
from layers.layer10_monetization.modules.universal_os.event_stream import EventStream
from layers.layer10_monetization.modules.universal_os.plugin_ecosystem import PluginEcosystem
from layers.layer10_monetization.modules.universal_os.service_registry import ServiceRegistry
from layers.layer10_monetization.modules.universal_os.api_gateway import APIGateway
from layers.layer10_monetization.modules.universal_os.authentication_manager import AuthenticationManager
from layers.layer10_monetization.modules.universal_os.configuration_manager import ConfigurationManager
from layers.layer10_monetization.modules.universal_os.resource_manager import ResourceManager
from layers.layer10_monetization.modules.universal_os.cache_manager import CacheManager
from layers.layer10_monetization.modules.universal_os.system_monitor import SystemMonitor
from layers.layer10_monetization.modules.universal_os.self_healing_engine import SelfHealingEngine
from layers.layer10_monetization.modules.universal_os.security_engine import SecurityEngine
from layers.layer10_monetization.modules.universal_os.system_metrics import SystemMetrics
from layers.layer10_monetization.modules.universal_os.backup_manager import BackupManager
from layers.layer10_monetization.modules.universal_os.version_manager import VersionManager

STAGES = ("observe", "research", "plan", "create", "quality",
          "publish", "analyze", "learn", "optimize", "evolve")
StageHandler = Callable[[str, Dict[str, Any]], Any]


class UniversalOSOrchestrator:
    """Own lifecycle and execute only explicitly registered pipeline stages."""

    def __init__(self) -> None:
        self.os = UniversalAIOS()
        self.kernel = SystemKernel()
        self.context = GlobalContextManager()
        self.memory = GlobalMemory()
        self.events = EventStream()
        self.plugins = PluginEcosystem()
        self.services = ServiceRegistry()
        self.api = APIGateway()
        self.auth = AuthenticationManager()
        self.config = ConfigurationManager()
        self.resources = ResourceManager()
        self.cache = CacheManager()
        self.monitor = SystemMonitor()
        self.healer = SelfHealingEngine()
        self.security = SecurityEngine()
        self.metrics = SystemMetrics()
        self.backup = BackupManager()
        self.version = VersionManager()
        self._pipeline_runs: List[Dict[str, Any]] = []
        self._max_pipeline_history = 10000
        self._lock = threading.RLock()
        self._stage_handlers: Dict[str, StageHandler] = {}

    def start(self) -> bool:
        if not self.os.start():
            return False
        self.events.publish("system_started", "orchestrator")
        self.metrics.record_event("system_start")
        return True

    def stop(self) -> bool:
        if not self.os.stop():
            return False
        self.events.publish("system_stopped", "orchestrator")
        self.metrics.record_event("system_stop")
        return True

    def register_stage(self, stage: str, handler: StageHandler) -> None:
        if stage not in STAGES:
            raise ValueError(f"Unknown pipeline stage: {stage}")
        if not callable(handler):
            raise ValueError("handler must be callable")
        with self._lock:
            self._stage_handlers[stage] = handler

    def run_pipeline(self, goal: str,
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not goal:
            raise ValueError("goal is required")
        if self.os.status()["state"] != "running":
            raise RuntimeError("orchestrator must be running before pipeline execution")

        started = time.time()
        pipeline_id = f"pipe_{uuid4().hex}"
        with self._lock:
            stage_handlers = dict(self._stage_handlers)
        ctx = dict(context or {})
        self.context.set("goal", pipeline_id, {"goal": goal, "context": ctx})
        pipeline: Dict[str, Any] = {
            "pipeline_id": pipeline_id, "goal": goal, "stages": {},
            "started_at": started, "status": "running",
        }

        for stage in STAGES:
            handler = stage_handlers.get(stage)
            stage_started = time.time()
            if handler is None:
                pipeline["stages"][stage] = {
                    "status": "not_configured", "timestamp": stage_started,
                }
                break
            try:
                result = handler(goal, ctx)
                pipeline["stages"][stage] = {
                    "status": "completed", "timestamp": stage_started,
                    "result": result,
                }
            except Exception as exc:
                pipeline["stages"][stage] = {
                    "status": "failed", "timestamp": stage_started,
                    "error": type(exc).__name__,
                }
                pipeline["status"] = "failed"
                break
        else:
            pipeline["status"] = "completed"

        pipeline["duration_ms"] = round((time.time() - started) * 1000, 1)
        with self._lock:
            self._pipeline_runs.append(pipeline)
            if len(self._pipeline_runs) > self._max_pipeline_history:
                del self._pipeline_runs[:-self._max_pipeline_history]
        event_type = "pipeline_completed" if pipeline["status"] == "completed" else "pipeline_failed"
        self.events.publish(event_type, "orchestrator",
                            {"pipeline_id": pipeline_id, "status": pipeline["status"]})
        self.metrics.record_event(event_type)
        return pipeline

    def get_health(self) -> Dict[str, Any]:
        return {
            "os": self.os.status(), "os_healthy": self.os.health(),
            "kernel": self.kernel.get_stats(), "context": self.context.get_stats(),
            "memory": self.memory.get_stats(), "events": self.events.get_stats(),
            "plugins": self.plugins.get_stats(), "services": self.services.get_stats(),
            "api": self.api.get_stats(), "auth": self.auth.get_stats(),
            "resources": self.resources.get_stats(), "cache": self.cache.get_stats(),
            "monitor": self.monitor.get_stats(), "healer": self.healer.get_stats(),
            "security": self.security.get_stats(), "metrics": self.metrics.get_stats(),
            "backup": self.backup.get_stats(), "version": self.version.get_stats(),
            "pipeline_runs": len(self._pipeline_runs),
            "configured_stages": sorted(self._stage_handlers),

            "max_pipeline_history": self._max_pipeline_history,
        }
