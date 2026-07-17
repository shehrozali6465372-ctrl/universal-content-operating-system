"""Workflow Coordinator — Main coordinator for reliable workflow execution."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List, Optional
from layers.layer10_monetization.modules.workflow_coordinator.workflow_definition import WorkflowDefinition
from layers.layer10_monetization.modules.workflow_coordinator.workflow_stage import WorkflowStage
from layers.layer10_monetization.modules.workflow_coordinator.execution_controller import ExecutionController
from layers.layer10_monetization.modules.workflow_coordinator.state_manager import StateManager
from layers.layer10_monetization.modules.workflow_coordinator.synchronization_manager import SynchronizationManager
from layers.layer10_monetization.modules.workflow_coordinator.checkpoint_manager import CheckpointManager
from layers.layer10_monetization.modules.workflow_coordinator.workflow_events import (
    WorkflowEventBus, WorkflowEvent,
    EVENT_WORKFLOW_STARTED, EVENT_STAGE_STARTED, EVENT_STAGE_COMPLETED,
    EVENT_STAGE_FAILED, EVENT_WORKFLOW_COMPLETED, EVENT_WORKFLOW_CANCELLED,
)
from layers.layer10_monetization.modules.workflow_coordinator.workflow_metrics import WorkflowMetrics
from layers.layer10_monetization.modules.workflow_coordinator.workflow_report import WorkflowReport

_WC_COUNTER = itertools.count(1)


class WorkflowCoordinator:
    """Coordinate reliable multi-layer workflow execution.

    Flow: Definition → Stages → Execute → Checkpoint → Report
    """

    def __init__(self) -> None:
        self.execution_controller = ExecutionController()
        self.state_manager = StateManager()
        self.sync_manager = SynchronizationManager()
        self.checkpoint_manager = CheckpointManager()
        self.event_bus = WorkflowEventBus()
        self.metrics = WorkflowMetrics()
        self._active_workflow: Optional[WorkflowDefinition] = None
        self._stages: List[WorkflowStage] = []
        self._reports: List[WorkflowReport] = []

    def start(self, definition: WorkflowDefinition) -> str:
        self._active_workflow = definition
        self._stages = []
        self.state_manager.reset()
        self.state_manager.set_state("running")

        for i, layer in enumerate(definition.stages):
            stage = WorkflowStage(layer, i)
            stage.max_retries = definition.max_retries
            self._stages.append(stage)

        self.event_bus.publish(WorkflowEvent(
            event_type=EVENT_WORKFLOW_STARTED,
            workflow_id=definition.workflow_id,
        ))

        self.checkpoint_manager.create(
            definition.workflow_id, "start",
            state={"state": "running"},
        )

        return definition.workflow_id

    def execute(self, executor: Callable,
                parallel_stages: Optional[List[str]] = None) -> WorkflowReport:
        if not self._active_workflow:
            raise ValueError("No active workflow. Call start() first.")

        definition = self._active_workflow
        start = time.time()
        report = WorkflowReport(definition.workflow_id, definition.name)
        parallel_stages = parallel_stages or []

        execution_batches = definition.get_execution_order()

        for batch in execution_batches:
            parallel_batch = [s for s in batch if s in parallel_stages]
            sequential_batch = [s for s in batch if s not in parallel_stages]

            if parallel_batch:
                para_stages = [self._get_stage(s) for s in parallel_batch if self._get_stage(s)]
                self.execution_controller.execute_parallel(para_stages, executor)
                for stage in para_stages:
                    self._record_stage(report, stage)

            for layer in sequential_batch:
                stage = self._get_stage(layer)
                if not stage:
                    continue
                self.state_manager.set_current_stage(layer)
                self.event_bus.publish(WorkflowEvent(
                    event_type=EVENT_STAGE_STARTED,
                    workflow_id=definition.workflow_id,
                ))

                result = self.execution_controller.execute_with_retry(
                    stage, executor, definition.max_retries,
                )

                self._record_stage(report, stage)

                self.event_bus.publish(WorkflowEvent(
                    event_type=EVENT_STAGE_COMPLETED if result.status == "completed" else EVENT_STAGE_FAILED,
                    workflow_id=definition.workflow_id,
                ))

                self.state_manager.complete_stage(layer)

                self.checkpoint_manager.create(
                    definition.workflow_id, layer,
                    state={"completed_stages": self.state_manager.get_completed_stages()},
                )

                if result.status == "failed":
                    self.state_manager.set_state("failed")
                else:
                    self.state_manager.set_state("running")

        report.total_duration_ms = (time.time() - start) * 1000
        report.success = len(report.stages_failed) == 0

        self.state_manager.set_state("completed" if report.success else "failed")
        self.metrics.record_run(
            success=report.success,
            duration_ms=report.total_duration_ms,
            retries=sum(s.retry_count for s in self._stages),
            stage_count=len(self._stages),
        )

        self.event_bus.publish(WorkflowEvent(
            event_type=EVENT_WORKFLOW_COMPLETED,
            workflow_id=definition.workflow_id,
        ))

        self._reports.append(report)
        return report

    def pause(self) -> bool:
        if self.state_manager.get_state() == "running":
            self.state_manager.set_state("paused")
            self.event_bus.publish(WorkflowEvent(
                event_type="workflow_paused",
                workflow_id=self._active_workflow.workflow_id if self._active_workflow else "",
            ))
            return True
        return False

    def resume(self) -> bool:
        if self.state_manager.get_state() == "paused":
            self.state_manager.set_state("running")
            self.event_bus.publish(WorkflowEvent(
                event_type="workflow_resumed",
                workflow_id=self._active_workflow.workflow_id if self._active_workflow else "",
            ))
            return True
        return False

    def cancel(self) -> bool:
        state = self.state_manager.get_state()
        if state in ("running", "paused"):
            self.state_manager.set_state("cancelled")
            for stage in self._stages:
                if not stage.is_terminal:
                    stage.status = "cancelled"
            self.event_bus.publish(WorkflowEvent(
                event_type=EVENT_WORKFLOW_CANCELLED,
                workflow_id=self._active_workflow.workflow_id if self._active_workflow else "",
            ))
            return True
        return False

    def retry_stage(self, layer: str, executor: Callable) -> bool:
        stage = self._get_stage(layer)
        if stage and stage.can_retry():
            self.event_bus.publish(WorkflowEvent(
                event_type="stage_retried",
                workflow_id=self._active_workflow.workflow_id if self._active_workflow else "",
            ))
            self.execution_controller.execute_with_retry(stage, executor, stage.max_retries)
            return stage.status == "completed"
        return False

    def complete(self) -> Optional[WorkflowReport]:
        return self._reports[-1] if self._reports else None

    def get_state(self) -> str:
        return self.state_manager.get_state()

    def get_stage_status(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._stages]

    def get_health(self) -> Dict[str, Any]:
        return {
            "active_workflow": self._active_workflow.workflow_id if self._active_workflow else None,
            "state": self.state_manager.get_state(),
            "stages": len(self._stages),
            "completed": len(self.state_manager.get_completed_stages()),
            "metrics": self.metrics.get_summary(),
            "sync": self.sync_manager.get_diagnostics(),
            "checkpoints": self.checkpoint_manager.get_stats(),
        }

    def get_recent_reports(self, count: int = 5) -> List[WorkflowReport]:
        return list(self._reports[-count:])

    def _get_stage(self, layer: str) -> Optional[WorkflowStage]:
        for s in self._stages:
            if s.layer == layer:
                return s
        return None

    def _record_stage(self, report: WorkflowReport, stage: WorkflowStage) -> None:
        report.add_stage(stage.stage_id, stage.layer, stage.status,
                        stage.duration_ms, stage.error or "")
        self.metrics.record_stage(stage.layer, stage.duration_ms,
                                  stage.status == "completed")
