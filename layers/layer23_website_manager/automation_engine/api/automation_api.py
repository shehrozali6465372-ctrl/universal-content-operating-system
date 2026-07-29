"""AutomationAPI — Unified interface for Dashboard and Learning Connector."""
from __future__ import annotations
from typing import Any, Dict


class AutomationAPI:
    """Provide controlled access to automation engine internals."""

    def __init__(self, parent: Any) -> None:
        self._parent = parent

    def get_status(self) -> Dict[str, Any]:
        return {
            "automation": self._parent.automation.get_stats(),
            "triggers": self._parent.triggers.get_stats(),
            "rules": self._parent.rules.get_stats(),
            "pipeline": self._parent.pipeline.get_stats(),
            "workers": self._parent.workers.get_stats(),
            "cron": self._parent.cron.get_stats(),
            "retry": self._parent.retry.get_stats(),
            "scaling": self._parent.scaling.get_stats(),
            "safety": self._parent.safety.get_stats(),
            "monitoring": self._parent.monitor.get_stats(),
            "recovery": self._parent.recovery.get_stats(),
            "optimizer": self._parent.optimizer.get_stats(),
        }

    def get_health(self) -> Dict[str, Any]:
        w = self._parent.workers.get_stats()
        p = self._parent.pipeline.get_stats()
        s = self._parent.safety.get_stats()
        return self._parent.monitor.get_status(w, p, s)

    def execute_workflow(self, workflow_id: str,
                         context: Dict[str, Any]) -> Dict[str, Any]:
        result = self._parent.pipeline.execute(workflow_id, context)
        return result.to_dict()
