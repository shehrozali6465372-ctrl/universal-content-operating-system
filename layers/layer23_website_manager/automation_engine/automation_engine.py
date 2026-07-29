"""AutomationEngine — Fully autonomous execution for Layer 23.

Orchestrates the complete automation lifecycle:
  Triggers → Rules → Pipeline → Workers → Monitoring → Recovery → Optimization

Flow:
    SchedulerOrchestrator (Module 11) → AutomationEngine (Module 12) → Learning Connector (Module 13)
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.automation_engine.automation.automation_manager import (
    AutomationManager,
)
from layers.layer23_website_manager.automation_engine.triggers.trigger_engine import (
    TriggerEngine,
)
from layers.layer23_website_manager.automation_engine.rules.rule_engine import (
    RuleEngine,
)
from layers.layer23_website_manager.automation_engine.pipeline.automation_pipeline import (
    AutomationPipeline,
)
from layers.layer23_website_manager.automation_engine.workers.worker_manager import (
    WorkerManager,
)
from layers.layer23_website_manager.automation_engine.cron.cron_manager import (
    CronManager,
)
from layers.layer23_website_manager.automation_engine.retry.smart_retry_engine import (
    SmartRetryEngine,
)
from layers.layer23_website_manager.automation_engine.scaling.auto_scaling_engine import (
    AutoScalingEngine,
)
from layers.layer23_website_manager.automation_engine.optimizer.workflow_optimizer import (
    WorkflowOptimizer,
)
from layers.layer23_website_manager.automation_engine.safety.safety_manager import (
    SafetyManager,
)
from layers.layer23_website_manager.automation_engine.monitoring.automation_monitor import (
    AutomationMonitor,
)
from layers.layer23_website_manager.automation_engine.recovery.emergency_recovery import (
    EmergencyRecovery,
)
from layers.layer23_website_manager.automation_engine.api.automation_api import (
    AutomationAPI,
)
from layers.layer23_website_manager.automation_engine.models.automation_models import (
    TriggerType, PipelineTask, AutomationResult, ExecutionRecord,
)
from layers.layer23_website_manager.automation_engine.exceptions import (
    AutomationError,
)

# Default pipeline task definitions for end-to-end publishing
_DEFAULT_PIPELINE = [
    ("Research", "research", "gather_topic_data", 1, []),
    ("Writing", "writing", "generate_article", 2, []),
    ("Website Publishing", "website_manager", "publish_to_website", 3, []),
    ("Pin Creation", "pinterest_pin_manager", "create_pin", 4, []),
    ("Affiliate Mapping", "affiliate_manager", "map_affiliate_product", 5, []),
    ("SEO Optimization", "seo_richpins_manager", "optimize_seo", 6, []),
    ("Publish", "pinterest_pin_manager", "publish_pin", 7, []),
    ("Traffic Tracking", "traffic_manager", "track_traffic", 8, []),
    ("Analytics", "analytics_manager", "collect_analytics", 9, []),
    ("Revenue Recording", "revenue_manager", "record_revenue", 10, []),
]


class AutomationEngine:
    """Fully autonomous execution engine for Layer 23.

    Automatically handles triggers, rules, pipeline execution, worker
    management, scaling, safety, monitoring, and recovery.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time: float = time.time()
        self._loop_running: bool = False
        self._loop_thread: Optional[threading.Thread] = None

        # Core components
        self.automation = AutomationManager()
        self.triggers = TriggerEngine()
        self.rules = RuleEngine()
        self.pipeline = AutomationPipeline()
        self.workers = WorkerManager(min_workers=2, max_workers=10)
        self.cron = CronManager()
        self.retry = SmartRetryEngine()
        self.scaling = AutoScalingEngine()
        self.optimizer = WorkflowOptimizer()
        self.safety = SafetyManager()
        self.monitor = AutomationMonitor()
        self.recovery = EmergencyRecovery()

        # API
        self.api = AutomationAPI(self)

        # Execution records
        self._records: List[ExecutionRecord] = []

        # Initialize default pipeline
        self._init_default_pipeline()
        # Initialize workers
        self.workers.initialize()

    def _init_default_pipeline(self) -> None:
        """Create the default end-to-end automation pipeline."""
        for name, module, action, order, deps in _DEFAULT_PIPELINE:
            self.pipeline.add_task(name, module, action, order, deps)

    def start(self) -> Dict[str, Any]:
        """Start the automation engine loop."""
        self.automation.start()
        with self._lock:
            if self._loop_running:
                return {"status": "already_running"}
            self._loop_running = True
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()
        return {"status": "started"}

    def stop(self) -> Dict[str, Any]:
        """Stop the automation engine loop."""
        with self._lock:
            self._loop_running = False
        return self.automation.stop()

    def pause(self) -> Dict[str, Any]:
        return self.automation.pause()

    def resume(self) -> Dict[str, Any]:
        return self.automation.resume()

    def _run_loop(self) -> None:
        """Main automation loop."""
        while True:
            with self._lock:
                if not self._loop_running:
                    break
            try:
                self._process_cron()
                self._evaluate_triggers()
                self._evaluate_rules()
                self._auto_scale()
                self._record_snapshot()
            except Exception:
                pass
            time.sleep(5)

    def _process_cron(self) -> None:
        if self.automation.status.value != "running":
            return
        fired = self.cron.tick()
        for sched_id in fired:
            sched = self.cron.get_schedule(sched_id)
            if sched and sched.workflow_id:
                result = self.pipeline.execute(sched.workflow_id)
                self._record_execution("cron", sched.name, result)

    def _evaluate_triggers(self) -> None:
        if self.automation.status.value != "running":
            return
        fired = self.triggers.evaluate_all()
        for trigger_id in fired:
            trigger = self.triggers.get_trigger(trigger_id)
            if trigger:
                result = self.pipeline.execute()
                self._record_execution("trigger", trigger.name, result)

    def _evaluate_rules(self) -> None:
        if self.automation.status.value != "running":
            return
        context = self._build_rule_context()
        self.rules.evaluate_all(context)

    def _build_rule_context(self) -> Dict[str, Any]:
        w = self.workers.get_stats()
        s = self.safety.get_stats()
        return {
            "active_workers": w["busy"],
            "idle_workers": w["idle"],
            "queue_size": w["queue_size"],
            "daily_executions": s["daily_executions"],
            "violations": s["violations"],
        }

    def _auto_scale(self) -> None:
        w = self.workers.get_stats()
        current = w["total_workers"]
        cpu = 0.0  # would come from real system metrics
        qsize = w["queue_size"]

        if self.scaling.should_scale_up(current, cpu, qsize):
            new_count = self.scaling.scale_up(current)
            self.workers.scale_to(new_count)
            self.monitor.record_warning(
                f"Scaled up workers: {current} → {new_count}", "scaling"
            )
        elif self.scaling.should_scale_down(current, cpu, qsize):
            new_count = self.scaling.scale_down(current)
            self.workers.scale_to(new_count)

    def _record_snapshot(self) -> None:
        data = {
            "workers": self.workers.get_stats(),
            "safety": self.safety.get_stats(),
        }
        self.monitor.record_snapshot(data)

    def _record_execution(self, trigger_type: str, trigger_name: str,
                          result: AutomationResult) -> None:
        record = ExecutionRecord(trigger=trigger_name, workflow_id=result.workflow_id)
        record.status = result.status
        record.duration_ms = result.duration_ms
        self._records.append(record)

    def execute_pipeline(self, workflow_id: str = "",
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the automation pipeline immediately."""
        if not self.safety.check_rate_limit():
            return {"status": "rate_limited", "error": "Rate limit exceeded"}
        if not self.safety.check_concurrent(self.workers.get_stats()["busy"]):
            return {"status": "concurrent_limit", "error": "Max concurrent reached"}
        if not self.safety.check_blocked_hours():
            return {"status": "blocked_hours", "error": "Currently in blocked hours"}

        worker = self.workers.get_idle_worker()
        if not worker:
            return {"status": "no_worker_available"}

        result = self.pipeline.execute(workflow_id, context)
        self.automation.record_execution(result.status == "completed")
        self.safety.record_execution()
        self._record_execution("manual", "manual_execution", result)
        self.workers.complete_task(worker.worker_id, result.status == "completed")
        return result.to_dict()

    def get_status(self) -> Dict[str, Any]:
        return {
            "module": "Automation Engine (Layer 23 / Module 12)",
            "version": "1.0.0",
            "automation": self.automation.get_stats(),
            "triggers": self.triggers.get_stats(),
            "rules": self.rules.get_stats(),
            "pipeline": self.pipeline.get_stats(),
            "workers": self.workers.get_stats(),
            "cron": self.cron.get_stats(),
            "retry": self.retry.get_stats(),
            "scaling": self.scaling.get_stats(),
            "safety": self.safety.get_stats(),
            "monitoring": self.monitor.get_stats(),
            "recovery": self.recovery.get_stats(),
            "optimizer": self.optimizer.get_stats(),
        }


# Singleton
_automation_instance: Optional[AutomationEngine] = None
_instance_lock = threading.Lock()


def get_automation_engine() -> AutomationEngine:
    """Get or create the singleton AutomationEngine instance."""
    global _automation_instance
    if _automation_instance is None:
        with _instance_lock:
            if _automation_instance is None:
                _automation_instance = AutomationEngine()
    return _automation_instance
