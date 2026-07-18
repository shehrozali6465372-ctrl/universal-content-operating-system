"""goal_memory_store.py — Goal memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class Goal:
    """An AI goal."""
    __slots__ = ("goal_id", "title", "description", "status", "priority",
                 "progress", "milestones", "created_at")
    _counter = 0

    def __init__(self, title: str, description: str = "", priority: int = 5) -> None:
        Goal._counter += 1
        self.goal_id: int = Goal._counter
        self.title = title
        self.description = description
        self.status: str = "active"
        self.priority = priority
        self.progress: float = 0.0
        self.milestones: List[Dict[str, Any]] = []
        import time
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.goal_id, "title": self.title, "status": self.status,
                "progress": self.progress, "priority": self.priority}


class GoalMemoryStore(BaseMemoryStore):
    """Stores goals and their progress."""

    def __init__(self, max_entries: int = 2000) -> None:
        super().__init__("goal", max_entries)
        self._goals: Dict[str, Goal] = {}

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "goal")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def add_goal(self, goal: Goal) -> None:
        self._goals[str(goal.goal_id)] = goal

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        return self._goals.get(goal_id)

    def get_active_goals(self) -> List[Goal]:
        return [g for g in self._goals.values() if g.status == "active"]

    def complete_goal(self, goal_id: str) -> bool:
        goal = self._goals.get(goal_id)
        if goal:
            goal.status = "completed"
            goal.progress = 1.0
            return True
        return False

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        active = len([g for g in self._goals.values() if g.status == "active"])
        base["goals"] = len(self._goals)
        base["active_goals"] = active
        return base
