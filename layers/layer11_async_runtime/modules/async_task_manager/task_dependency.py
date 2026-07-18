"""TaskDependency — Manage task dependencies."""
from __future__ import annotations
from typing import Dict, List, Set
class TaskDependency:
    def __init__(self): self._deps: Dict[str, Set[str]] = {}
    def add(self, task_id: str, depends_on: str):
        self._deps.setdefault(task_id, set()).add(depends_on)
    def get(self, task_id: str) -> List[str]: return list(self._deps.get(task_id, set()))
    def is_satisfied(self, task_id: str, completed: Set[str]) -> bool:
        return all(d in completed for d in self._deps.get(task_id, set()))
    def get_stats(self): return {"total_dependencies": sum(len(v) for v in self._deps.values())}
