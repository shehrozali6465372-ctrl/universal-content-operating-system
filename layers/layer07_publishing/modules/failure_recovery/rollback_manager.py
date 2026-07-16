"""Rollback Manager — Undo partial publishes and clean up resources."""
from __future__ import annotations
import itertools
from typing import Any, Callable, Dict, List

_ROLLBACK_COUNTER = itertools.count(1)


class RollbackAction:
    """Single rollback action to undo."""

    __slots__ = ("action_id", "name", "executed", "rolled_back", "error", "metadata")

    def __init__(self, name: str) -> None:
        self.action_id: str = f"rb_{next(_ROLLBACK_COUNTER)}"
        self.name = name
        self.executed = False
        self.rolled_back = False
        self.error: str = ""
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "name": self.name,
            "executed": self.executed,
            "rolled_back": self.rolled_back,
            "error": self.error,
        }


class RollbackManager:
    """Manage rollback of partial publishing operations."""

    def __init__(self) -> None:
        self._actions: List[RollbackAction] = []
        self._rollback_fns: List[Callable[[], bool]] = []
        self._rollback_count = 0

    def add_action(self, name: str, rollback_fn: Callable[[], bool]) -> RollbackAction:
        action = RollbackAction(name)
        action.executed = True
        self._actions.append(action)
        self._rollback_fns.append(rollback_fn)
        return action

    def execute_rollback(self) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        all_success = True

        for i in reversed(range(len(self._rollback_fns))):
            action = self._actions[i]
            try:
                success = self._rollback_fns[i]()
                action.rolled_back = success
                if not success:
                    all_success = False
            except Exception as e:
                action.rolled_back = False
                action.error = str(e)[:200]
                all_success = False
            results.append(action.to_dict())

        self._rollback_count += 1
        return {
            "success": all_success,
            "actions": len(results),
            "results": results,
            "rollback_count": self._rollback_count,
        }

    def get_actions(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self._actions]

    def undo_published_media(self, media_ids: List[str]) -> bool:
        """Cleanup uploaded media (stub — delegates to platform plugin)."""
        return True

    def restore_previous_state(self, state_snapshot: Dict[str, Any]) -> bool:
        """Restore a previously saved state (stub)."""
        return True

    @property
    def action_count(self) -> int:
        return len(self._actions)

    @property
    def rollback_count(self) -> int:
        return self._rollback_count
