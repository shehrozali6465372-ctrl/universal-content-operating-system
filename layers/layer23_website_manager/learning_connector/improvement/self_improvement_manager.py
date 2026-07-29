"""SelfImprovementManager — Automatically improve workflows and strategies."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.learning_connector.models.learning_models import (
    ImprovementAction, Recommendation,
)


class SelfImprovementManager:
    """Execute self-improvement actions based on learning."""

    def __init__(self) -> None:
        self._actions: List[ImprovementAction] = []
        self._handlers: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._total_improvements: int = 0

    def register_handler(self, action_type: str, handler: Any) -> None:
        with self._lock:
            self._handlers[action_type] = handler

    def apply_improvement(self, action_type: str, target_module: str = "",
                          description: str = "",
                          params: Optional[Dict[str, Any]] = None) -> ImprovementAction:
        action = ImprovementAction(action_type, target_module, description)
        handler = self._handlers.get(action_type)
        if handler:
            try:
                result = handler(params or {})
                action.result = result if isinstance(result, dict) else {"result": result}
                action.status = "completed"
            except Exception as exc:
                action.status = "failed"
                action.result = {"error": str(exc)}
        else:
            action.status = "simulated"
            action.result = {"note": f"No handler for {action_type}"}

        with self._lock:
            self._actions.append(action)
            self._total_improvements += 1
        return action

    def apply_recommendations(self, recommendations: List[Recommendation]) -> int:
        count = 0
        for rec in recommendations:
            if rec.status != "pending":
                continue
            self.apply_improvement(
                action_type=f"implement_{rec.category}",
                target_module=rec.category,
                description=rec.title,
            )
            rec.status = "implemented"
            rec.implemented_at = time.time()
            count += 1
        return count

    def get_actions(self, status: Optional[str] = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            actions = self._actions
            if status:
                actions = [a for a in actions if a.status == status]
            return [a.to_dict() for a in actions[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._actions)
            completed = sum(1 for a in self._actions if a.status == "completed")
            failed = sum(1 for a in self._actions if a.status == "failed")
            return {
                "total_actions": total,
                "completed": completed,
                "failed": failed,
                "success_rate": round((completed / max(total, 1)) * 100, 1),
                "handlers_registered": len(self._handlers),
            }
