"""ResearchManager — Main research brain orchestrating all intelligence."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_RM_COUNTER = itertools.count(1)


class ResearchTask:
    """A research task."""

    __slots__ = ("task_id", "topic", "platforms", "priority", "status",
                 "results", "created_at", "completed_at")

    def __init__(self, topic: str = "", platforms: Optional[List[str]] = None) -> None:
        self.task_id: str = f"rtask_{next(_RM_COUNTER)}"
        self.topic = topic
        self.platforms = platforms or ["universal"]
        self.priority: int = 1
        self.status: str = "pending"
        self.results: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.completed_at: Optional[float] = None


class ResearchManager:
    """Orchestrate all research activities across platforms."""

    def __init__(self) -> None:
        self._tasks: List[ResearchTask] = []
        self._research_cache: Dict[str, Any] = {}
        self._is_running: bool = False
        self._events: List[Dict[str, Any]] = []

    def start(self) -> bool:
        self._is_running = True
        self._events.append({"event": "research_started", "time": time.time()})
        return True

    def stop(self) -> bool:
        self._is_running = False
        self._events.append({"event": "research_stopped", "time": time.time()})
        return True

    def create_task(self, topic: str, platforms: Optional[List[str]] = None,
                    priority: int = 1) -> ResearchTask:
        task = ResearchTask(topic, platforms)
        task.priority = priority
        self._tasks.append(task)
        return task

    def execute_task(self, task_id: str) -> Optional[ResearchTask]:
        for task in self._tasks:
            if task.task_id == task_id:
                task.status = "completed"
                task.completed_at = time.time()
                task.results = {"topic": task.topic, "platforms": task.platforms,
                                "findings": f"Research on {task.topic} completed"}
                return task
        return None

    def get_pending_tasks(self) -> List[ResearchTask]:
        return [t for t in self._tasks if t.status == "pending"]

    def get_completed_tasks(self) -> List[ResearchTask]:
        return [t for t in self._tasks if t.status == "completed"]

    def research(self, topic: str, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        task = self.create_task(topic, platforms)
        self.execute_task(task.task_id)
        return task.results

    def get_stats(self) -> Dict[str, Any]:
        return {"total_tasks": len(self._tasks),
                "completed": len(self.get_completed_tasks()),
                "pending": len(self.get_pending_tasks()),
                "running": self._is_running}
