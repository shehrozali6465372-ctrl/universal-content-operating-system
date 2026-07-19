"""AITaskManager — manage individual AI tasks."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from .models import Task, TaskStatus

class AITaskManager:
    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}
    def create(self, name: str, input_data: Dict[str, Any] | None = None,
               priority: int = 5) -> Task:
        task = Task(name=name, input_data=input_data or {}, priority=priority)
        self._tasks[task.task_id] = task; return task
    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)
    def complete(self, task_id: str, output: Dict[str, Any] | None = None) -> bool:
        task = self._tasks.get(task_id)
        if task: task.status = TaskStatus.COMPLETED; task.output_data = output or {}; return True
        return False
    def fail(self, task_id: str, error: str) -> bool:
        task = self._tasks.get(task_id)
        if task: task.status = TaskStatus.FAILED; task.error = error; return True
        return False
    def list_by_status(self, status: TaskStatus) -> List[Task]:
        return [t for t in self._tasks.values() if t.status == status]
    def count(self) -> int: return len(self._tasks)
    def clear(self) -> None: self._tasks.clear()
    def to_dict(self) -> Dict[str, Any]:
        return {"total": self.count(),
                "by_status": {s.value: len(self.list_by_status(s)) for s in TaskStatus}}
