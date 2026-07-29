"""OrchestratorAPI — Unified API for Automation Engine and Learning Connector."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class OrchestratorAPI:
    """Provide controlled access to orchestrator internals."""

    def __init__(self, parent: Any) -> None:
        self._parent = parent

    def get_status(self) -> Dict[str, Any]:
        return {
            "workflows": self._parent.workflows.get_stats(),
            "scheduler": self._parent.scheduler.get_stats(),
            "queue": self._parent.queue.get_stats(),
            "executor": self._parent.executor.get_stats(),
            "retry": self._parent.retry.get_stats(),
            "events": self._parent.events.get_stats(),
            "notifications": self._parent.notifications.get_stats(),
            "monitoring": self._parent.monitoring.get_stats(),
            "recovery": self._parent.recovery.get_stats(),
            "resources": self._parent.resources.get_stats(),
            "analytics": self._parent.analytics.get_stats(),
        }

    def get_health(self) -> Dict[str, Any]:
        scheduler_stats = self._parent.scheduler.get_stats()
        return self._parent.monitoring.check_health(scheduler_stats)

    def get_summary(self) -> Dict[str, Any]:
        s = self._parent.scheduler.get_stats()
        q = self._parent.queue.get_stats()
        e = self._parent.executor.get_stats()
        return {
            "total_jobs": s["total"],
            "active_jobs": s["running"],
            "pending_jobs": s["pending"] + s["queued"] if "queued" in s else s["pending"],
            "completed_jobs": s["completed"],
            "failed_jobs": s["failed"],
            "queue_active": q["total_active"],
            "queue_retry": q["retry"],
            "executions": e["total_executions"],
            "active_executions": e["active"],
        }
