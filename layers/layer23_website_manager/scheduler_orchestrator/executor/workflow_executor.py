"""WorkflowExecutor — Execute workflow steps, manage parallel/batch execution."""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional, Set

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    WorkflowDefinition, WorkflowStep, WorkflowResult, WorkflowStatus, ExecutionLog,
)
from layers.layer23_website_manager.scheduler_orchestrator.dependencies.dependency_manager import (
    DependencyManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.exceptions import (
    ExecutionError,
)


class WorkflowExecutor:
    """Execute workflow definitions step by step."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable] = {}
        self._execution_logs: List[ExecutionLog] = []
        self._active_executions: Dict[str, WorkflowResult] = {}
        self._lock = threading.RLock()

    def register_handler(self, action: str, handler: Callable) -> None:
        self._handlers[action] = handler

    def execute(self, workflow: WorkflowDefinition,
                dep_manager: DependencyManager,
                context: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        wf_result = WorkflowResult(
            workflow_id=workflow.workflow_id,
            job_id=f"exec_{workflow.workflow_id}_{int(time.time())}",
        )
        with self._lock:
            self._active_executions[wf_result.job_id] = wf_result

        workflow.status = WorkflowStatus.RUNNING
        completed: Set[str] = set()
        failed: Set[str] = set()
        ctx = dict(context or {})

        try:
            while len(completed) + len(failed) < len(workflow.steps):
                ready = dep_manager.get_ready_steps(
                    workflow.steps, completed, failed
                )
                if not ready:
                    if len(completed) + len(failed) < len(workflow.steps):
                        raise ExecutionError(
                            "Deadlock: no steps ready but steps remain"
                        )
                    break

                for step in ready:
                    log = self._execute_step(step, ctx)
                    self._execution_logs.append(log)
                    if log.status == "completed":
                        completed.add(step.step_id)
                        wf_result.steps_results[step.step_id] = {
                            "status": "completed", "result": step.result,
                        }
                    else:
                        failed.add(step.step_id)
                        wf_result.steps_results[step.step_id] = {
                            "status": "failed", "error": log.error,
                        }

            if failed:
                wf_result.status = "completed_with_errors"
            else:
                wf_result.status = "completed"
        except Exception as exc:
            wf_result.error = str(exc)
            wf_result.status = "failed"
        finally:
            wf_result.complete(wf_result.status)
            workflow.status = (
                WorkflowStatus.COMPLETED if wf_result.status == "completed"
                else WorkflowStatus.FAILED
            )
            with self._lock:
                self._active_executions.pop(wf_result.job_id, None)

        return wf_result

    def _execute_step(self, step: WorkflowStep,
                      context: Dict[str, Any]) -> ExecutionLog:
        log = ExecutionLog(
            job_id="", workflow_id="", step_name=step.name,
            module=step.module, action=step.action,
        )
        step.started_at = time.time()
        step.status = "running"

        try:
            handler = self._handlers.get(step.action)
            if handler:
                result = handler(step, context)
                step.result = result if isinstance(result, dict) else {"result": result}
            else:
                step.result = {"status": "simulated", "module": step.module}

            step.completed_at = time.time()
            step.status = "completed"
            log.status = "completed"
            log.duration_ms = (step.completed_at - step.started_at) * 1000

        except Exception as exc:
            step.completed_at = time.time()
            step.status = "failed"
            step.error = str(exc)
            log.status = "failed"
            log.error = str(exc)
            log.duration_ms = (step.completed_at - step.started_at) * 1000

        log.timestamp = step.completed_at or time.time()
        return log

    def execute_batch(self, workflows: List[WorkflowDefinition],
                      dep_manager: DependencyManager) -> List[WorkflowResult]:
        return [self.execute(wf, dep_manager) for wf in workflows]

    def get_execution_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [log.to_dict() for log in self._execution_logs[-limit:]]

    def get_active_executions(self) -> int:
        with self._lock:
            return len(self._active_executions)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_executions": len(self._execution_logs),
                "active": len(self._active_executions),
                "handlers_registered": len(self._handlers),
                "completed": sum(1 for l in self._execution_logs if l.status == "completed"),
                "failed": sum(1 for l in self._execution_logs if l.status == "failed"),
            }
