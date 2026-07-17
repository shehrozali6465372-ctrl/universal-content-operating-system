"""PlanMemory — Store successful and failed plans."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_PM_COUNTER = itertools.count(1)


class PlanMemoryEntry:
    """A stored plan memory."""

    __slots__ = ("entry_id", "plan_type", "goal", "steps_count",
                 "success", "duration_ms", "tags", "created_at")

    def __init__(self, plan_type: str = "", goal: str = "") -> None:
        self.entry_id: str = f"pmem_{next(_PM_COUNTER)}"
        self.plan_type = plan_type
        self.goal = goal
        self.steps_count: int = 0
        self.success: bool = False
        self.duration_ms: float = 0.0
        self.tags: List[str] = []
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id, "plan_type": self.plan_type,
            "success": self.success, "duration_ms": round(self.duration_ms, 1),
        }


class PlanMemory:
    """Store and retrieve plan memories."""

    def __init__(self, max_entries: int = 2000) -> None:
        self._max_entries = max_entries
        self._entries: List[PlanMemoryEntry] = []

    def store(self, plan_type: str, goal: str, steps_count: int = 0,
              success: bool = False, duration_ms: float = 0.0,
              tags: Optional[List[str]] = None) -> PlanMemoryEntry:
        entry = PlanMemoryEntry(plan_type, goal)
        entry.steps_count = steps_count
        entry.success = success
        entry.duration_ms = duration_ms
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def search(self, plan_type: str = "", tag: str = "",
               success_only: bool = False, limit: int = 50) -> List[PlanMemoryEntry]:
        results = self._entries
        if plan_type:
            results = [e for e in results if e.plan_type == plan_type]
        if tag:
            results = [e for e in results if tag in e.tags]
        if success_only:
            results = [e for e in results if e.success]
        return results[-limit:]

    def get_successful_plans(self) -> List[PlanMemoryEntry]:
        return [e for e in self._entries if e.success]

    def get_failed_plans(self) -> List[PlanMemoryEntry]:
        return [e for e in self._entries if not e.success]

    def get_templates(self) -> Dict[str, int]:
        templates: Dict[str, int] = {}
        for e in self._entries:
            if e.success:
                templates[e.plan_type] = templates.get(e.plan_type, 0) + 1
        return templates

    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._entries),
                "successful": len(self.get_successful_plans()),
                "failed": len(self.get_failed_plans())}
