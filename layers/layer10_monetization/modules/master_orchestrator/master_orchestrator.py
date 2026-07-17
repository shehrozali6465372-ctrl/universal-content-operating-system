"""Master Orchestrator — Central brain coordinating all layers (1–9)."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List, Optional

from layers.layer10_monetization.modules.master_orchestrator.orchestration_context import OrchestrationContext
from layers.layer10_monetization.modules.master_orchestrator.layer_router import LayerRouter
from layers.layer10_monetization.modules.master_orchestrator.dependency_manager import LayerDependencies
from layers.layer10_monetization.modules.master_orchestrator.execution_scheduler import ExecutionScheduler
from layers.layer10_monetization.modules.master_orchestrator.system_health_monitor import SystemHealthMonitor
from layers.layer10_monetization.modules.master_orchestrator.event_bus import SystemEventBus, SystemEvent
from layers.layer10_monetization.modules.master_orchestrator.orchestrator_metrics import OrchestratorMetrics
from layers.layer10_monetization.modules.master_orchestrator.orchestrator_report import OrchestratorReport
from layers.layer10_monetization.modules.master_orchestrator.workflow_engine import WorkflowEngine

_MO_COUNTER = itertools.count(1)

# Event type constants
EVENT_WORKFLOW_STARTED = "workflow_started"
EVENT_WORKFLOW_COMPLETED = "workflow_completed"
EVENT_WORKFLOW_FAILED = "workflow_failed"
EVENT_LAYER_COMPLETED = "layer_completed"
EVENT_LAYER_FAILED = "layer_failed"


class MasterOrchestrator:
    """Central orchestration engine coordinating Layers 1–9.

    Flow: Request → Context → Workflow → Layer Router → Layers 1–9 → Report
    """

    def __init__(self) -> None:
        self.context: Optional[OrchestrationContext] = None
        self.router = LayerRouter()
        self.dependencies = LayerDependencies()
        self.scheduler = ExecutionScheduler()
        self.health_monitor = SystemHealthMonitor()
        self.event_bus = SystemEventBus()
        self.metrics = OrchestratorMetrics()
        self.workflow_engine = WorkflowEngine()
        self._layer_handlers: Dict[str, Callable] = {}
        self._reports: List[OrchestratorReport] = []
        self._running: bool = False

    def register_layer_handler(self, layer: str, handler: Callable) -> None:
        self._layer_handlers[layer] = handler

    def start(self, user_id: str = "", session_id: str = "",
              metadata: Optional[Dict[str, Any]] = None) -> OrchestrationContext:
        self.context = OrchestrationContext(user_id, session_id)
        if metadata:
            self.context.metadata = dict(metadata)
        self.context.update_state("started")
        self._running = True

        self.event_bus.publish(SystemEvent(
            event_type=EVENT_WORKFLOW_STARTED,
            source="master_orchestrator",
        ))

        # Register all layers as healthy
        for layer in self.dependencies.LAYER_ORDER:
            self.health_monitor.register_component(layer)

        return self.context

    def execute(self, task_types: List[str],
                context: Optional[OrchestrationContext] = None) -> OrchestratorReport:
        ctx = context or self.context
        if not ctx:
            ctx = OrchestrationContext()
            self.context = ctx

        ctx.update_state("executing")
        start = time.time()
        report = OrchestratorReport(ctx.request_id)

        # Resolve layers from task types
        layers = []
        for task in task_types:
            layer = self.router.get_layer_for_task(task)
            if layer:
                layers.append(layer)

        # Deduplicate while preserving order
        seen = set()
        unique_layers = []
        for l in layers:
            if l not in seen:
                seen.add(l)
                unique_layers.append(l)

        # Resolve execution order
        ordered_layers = self.dependencies.resolve_order(unique_layers)

        # Execute each layer
        for layer in ordered_layers:
            ctx.set_layer(layer)
            layer_start = time.time()
            try:
                handler = self._layer_handlers.get(layer)
                if handler:
                    output = handler(ctx)
                else:
                    output = {"layer": layer, "status": "completed", "no_handler": True}

                ctx.complete_layer(layer, output)
                report.add_layer_output(layer, output)

                self.health_monitor.check(layer, status="healthy",
                                          latency_ms=(time.time() - layer_start) * 1000)

                self.event_bus.publish(SystemEvent(
                    event_type=EVENT_LAYER_COMPLETED,
                    source=layer,
                ))
            except Exception as e:
                ctx.add_error(layer, str(e))
                report.add_failure(layer, str(e))

                self.health_monitor.check(layer, status="critical",
                                          message=str(e))
                self.metrics.record_layer_failure(layer)

                self.event_bus.publish(SystemEvent(
                    event_type=EVENT_LAYER_FAILED,
                    source=layer,
                ))

        report.duration_ms = (time.time() - start) * 1000
        report.success = len(report.layers_failed) == 0
        report.set_metrics(self.metrics.get_summary())

        self.metrics.record_run(
            success=report.success,
            duration_ms=report.duration_ms,
            layers_executed=len(report.layers_executed),
            layer_names=report.layers_executed,
        )

        ctx.update_state("completed" if report.success else "failed")
        self._running = False

        self.event_bus.publish(SystemEvent(
            event_type=EVENT_WORKFLOW_COMPLETED if report.success else EVENT_WORKFLOW_FAILED,
            source="master_orchestrator",
        ))

        self._reports.append(report)
        return report

    def pause(self) -> bool:
        if self._running:
            self._running = False
            if self.context:
                self.context.update_state("paused")
            return True
        return False

    def resume(self) -> bool:
        if self.context and self.context.workflow_state == "paused":
            self._running = True
            self.context.update_state("resumed")
            return True
        return False

    def cancel(self) -> bool:
        if self._running or self.context:
            self._running = False
            if self.context:
                self.context.update_state("cancelled")
            self.event_bus.publish(SystemEvent(
                event_type="workflow_cancelled",
                source="master_orchestrator",
            ))
            return True
        return False

    def status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "context": self.context.to_dict() if self.context else None,
            "health": self.health_monitor.get_overall_status(),
            "metrics": self.metrics.get_summary(),
            "report_count": len(self._reports),
        }

    def shutdown(self) -> Dict[str, Any]:
        self._running = False
        if self.context:
            self.context.update_state("shutdown")
        return {
            "status": "shutdown",
            "total_reports": len(self._reports),
            "metrics": self.metrics.get_summary(),
        }

    def get_health(self) -> Dict[str, Any]:
        return self.health_monitor.get_diagnostics()

    def get_recent_reports(self, count: int = 5) -> List[OrchestratorReport]:
        return list(self._reports[-count:])

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def execution_count(self) -> int:
        return len(self._reports)
