"""SchedulerOrchestrator — Master workflow orchestration for Layer 23.

Coordinates the complete pipeline:
Research → Writing → Website → Pinterest → Affiliate → SEO → Traffic → Analytics → Revenue

Flow:
    Modules 1-10 → SchedulerOrchestrator → Automation Engine (Module 12)
"""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional

from layers.layer23_website_manager.scheduler_orchestrator.workflow.workflow_manager import (
    WorkflowManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.scheduler.task_scheduler import (
    TaskScheduler,
)
from layers.layer23_website_manager.scheduler_orchestrator.queue.job_queue_manager import (
    JobQueueManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.dependencies.dependency_manager import (
    DependencyManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.executor.workflow_executor import (
    WorkflowExecutor,
)
from layers.layer23_website_manager.scheduler_orchestrator.retry.retry_manager import (
    RetryManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.resources.resource_manager import (
    ResourceManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.events.event_manager import (
    EventManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.notifications.notification_manager import (
    NotificationManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.monitoring.monitoring_manager import (
    MonitoringManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.recovery.recovery_manager import (
    RecoveryManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.analytics.workflow_analytics import (
    WorkflowAnalyticsCollector,
)
from layers.layer23_website_manager.scheduler_orchestrator.api.orchestrator_api import (
    OrchestratorAPI,
)
from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    WorkflowDefinition, WorkflowStep, ScheduledJob, Priority, JobStatus,
)
from layers.layer23_website_manager.scheduler_orchestrator.exceptions import (
    SchedulerError, WorkflowError,
)

# Default publishing workflow steps
_PUBLISHING_WORKFLOW_STEPS = [
    ("Research", "research", "gather_topic_data", []),
    ("Writing", "writing", "generate_article", ["Research"]),
    ("Website", "website_manager", "publish_to_website", ["Writing"]),
    ("Pinterest Account", "pinterest_account_manager", "select_account", ["Website"]),
    ("Pinterest Board", "pinterest_board_manager", "select_board", ["Pinterest Account"]),
    ("Pin Creation", "pinterest_pin_manager", "create_pin", ["Pinterest Board"]),
    ("Affiliate Mapping", "affiliate_manager", "map_affiliate_product", ["Pin Creation"]),
    ("SEO Optimization", "seo_richpins_manager", "optimize_seo", ["Affiliate Mapping"]),
    ("Publish", "pinterest_pin_manager", "publish_pin", ["SEO Optimization"]),
    ("Traffic Tracking", "traffic_manager", "track_traffic", ["Publish"]),
    ("Analytics", "analytics_manager", "collect_analytics", ["Traffic Tracking"]),
    ("Revenue", "revenue_manager", "record_revenue", ["Analytics"]),
]


class SchedulerOrchestrator:
    """Master orchestrator for Layer 23 workflow management.

    Coordinates all 10 modules through a unified scheduling, execution,
    monitoring, and recovery system.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time: float = time.time()
        self._running: bool = False
        self._loop_thread: Optional[threading.Thread] = None

        # Core components
        self.workflows = WorkflowManager()
        self.scheduler = TaskScheduler()
        self.queue = JobQueueManager()
        self.dependencies = DependencyManager()
        self.executor = WorkflowExecutor()
        self.retry = RetryManager()
        self.resources = ResourceManager(max_workers=10)
        self.events = EventManager()
        self.notifications = NotificationManager()
        self.monitoring = MonitoringManager()
        self.recovery = RecoveryManager()
        self.analytics = WorkflowAnalyticsCollector()

        # API
        self.api = OrchestratorAPI(self)

        # Initialize default publishing workflow
        self._init_default_workflow()

    def _init_default_workflow(self) -> None:
        """Create the default end-to-end publishing workflow."""
        wf = self.workflows.create_workflow(
            name="End-to-End Publishing",
            description="Complete content publishing pipeline: Research → Revenue",
            priority=Priority.NORMAL,
            tags=["publishing", "default", "end_to_end"],
        )
        step_map: Dict[str, str] = {}
        for step_name, module, action, deps in _PUBLISHING_WORKFLOW_STEPS:
            dep_ids = [step_map.get(d) for d in deps if d in step_map]
            step = WorkflowStep(
                name=step_name, module=module, action=action,
                depends_on=dep_ids,
            )
            wf.add_step(step)
            step_map[step_name] = step.step_id

        self.workflows.activate_workflow(wf.workflow_id)

    def start(self) -> Dict[str, Any]:
        """Start the orchestrator loop."""
        with self._lock:
            if self._running:
                return {"status": "already_running"}
            self._running = True
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()
        self.events.emit("orchestrator_started", "scheduler_orchestrator")
        return {"status": "started"}

    def stop(self) -> Dict[str, Any]:
        """Stop the orchestrator loop."""
        with self._lock:
            self._running = False
        self.events.emit("orchestrator_stopped", "scheduler_orchestrator")
        return {"status": "stopped"}

    def _run_loop(self) -> None:
        """Main orchestrator loop."""
        while True:
            with self._lock:
                if not self._running:
                    break
            try:
                self._process_due_jobs()
                self._process_retry_queue()
                self._update_metrics()
            except Exception:
                pass
            time.sleep(1)

    def _process_due_jobs(self) -> None:
        """Process jobs that are due for execution."""
        due_jobs = self.scheduler.get_due_jobs()
        for job in due_jobs:
            if self.resources.acquire_worker():
                self.scheduler.mark_running(job.job_id)
                self.queue.enqueue(job)
                self.events.emit("job_enqueued", "scheduler",
                                 {"job_id": job.job_id})

    def _process_retry_queue(self) -> None:
        """Process jobs in the retry queue."""
        retry_job = self.queue.dequeue_retry()
        while retry_job:
            if self.retry.should_retry(retry_job):
                self.queue.enqueue(retry_job)
                self.retry.record_retry(retry_job)
            retry_job = self.queue.dequeue_retry()

    def _update_metrics(self) -> None:
        """Record periodic resource metrics."""
        metrics = self.resources.get_metrics()
        self.monitoring.record_metrics(metrics)

    def submit_workflow(self, workflow_id: str,
                        scheduled_time: Optional[float] = None,
                        delay_seconds: float = 0) -> str:
        """Submit a workflow for execution."""
        wf = self.workflows.get_workflow(workflow_id)
        if not wf:
            raise WorkflowError(f"Workflow '{workflow_id}' not found")

        job = self.scheduler.schedule_job(
            workflow_id=workflow_id,
            name=wf.name,
            priority=wf.priority,
            scheduled_time=scheduled_time,
            delay_seconds=delay_seconds,
        )
        self.events.emit("workflow_submitted", "scheduler",
                         {"workflow_id": workflow_id, "job_id": job.job_id})
        return job.job_id

    def execute_workflow(self, workflow_id: str,
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a workflow immediately."""
        wf = self.workflows.get_workflow(workflow_id)
        if not wf:
            raise WorkflowError(f"Workflow '{workflow_id}' not found")

        result = self.executor.execute(wf, self.dependencies, context)
        self.events.emit("workflow_executed", "executor",
                         {"workflow_id": workflow_id,
                          "status": result.status})

        # Send notification
        level = "success" if result.status == "completed" else "error"
        self.notifications.send(
            title=f"Workflow '{wf.name}' {result.status}",
            message=f"Duration: {result.duration_ms:.0f}ms",
            level=level,
            source="executor",
        )
        return result.to_dict()

    def execute_default_publishing(self,
                                   context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the default end-to-end publishing workflow."""
        workflows = self.workflows.get_workflows_by_tag("publishing")
        if not workflows:
            raise WorkflowError("No publishing workflow found")
        return self.execute_workflow(workflows[0].workflow_id, context)

    def get_status(self) -> Dict[str, Any]:
        """Get full orchestrator status."""
        return {
            "module": "Scheduler & Workflow Orchestrator (Layer 23 / Module 11)",
            "version": "1.0.0",
            "running": self._running,
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "workflows": self.workflows.get_stats(),
            "scheduler": self.scheduler.get_stats(),
            "queue": self.queue.get_stats(),
            "executor": self.executor.get_stats(),
            "retry": self.retry.get_stats(),
            "resources": self.resources.get_stats(),
            "events": self.events.get_stats(),
            "notifications": self.notifications.get_stats(),
            "recovery": self.recovery.get_stats(),
            "analytics": self.analytics.get_stats(),
        }


# Singleton
_scheduler_instance: Optional[SchedulerOrchestrator] = None
_instance_lock = threading.Lock()


def get_scheduler() -> SchedulerOrchestrator:
    """Get or create the singleton SchedulerOrchestrator instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        with _instance_lock:
            if _scheduler_instance is None:
                _scheduler_instance = SchedulerOrchestrator()
    return _scheduler_instance
