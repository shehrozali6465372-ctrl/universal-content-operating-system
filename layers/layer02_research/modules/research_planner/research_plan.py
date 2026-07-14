"""
Research Plan
Layer 2: Research Engine — Module 9

Research plan data model:
- Plan structure
- Task representation
- Plan status tracking
- Plan serialization
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional


class PlanTask:
    """A single task in a research plan."""

    __slots__ = (
        "task_id", "name", "description", "module",
        "priority", "status", "estimated_time_min",
        "estimated_api_calls", "estimated_memory_mb",
        "dependencies", "result", "confidence",
        "started_at", "completed_at",
    )

    PRIORITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "BACKGROUND"]
    STATUSES = ["pending", "ready", "running", "completed", "failed", "skipped"]

    def __init__(
        self,
        name: str,
        description: str = "",
        module: str = "",
        priority: str = "MEDIUM",
        estimated_time_min: float = 5.0,
        estimated_api_calls: int = 0,
        estimated_memory_mb: float = 10.0,
        dependencies: Optional[List[str]] = None,
    ):
        self.task_id = f"task_{hash(name) % 1000000}"
        self.name = name
        self.description = description
        self.module = module
        self.priority = priority if priority in self.PRIORITIES else "MEDIUM"
        self.status = "pending"
        self.estimated_time_min = max(0.0, estimated_time_min)
        self.estimated_api_calls = max(0, estimated_api_calls)
        self.estimated_memory_mb = max(0.0, estimated_memory_mb)
        self.dependencies = dependencies or []
        self.result: Optional[Dict] = None
        self.confidence = 0.0
        self.started_at = ""
        self.completed_at = ""

    def start(self):
        self.status = "running"
        self.started_at = datetime.now(timezone.utc).isoformat()

    def complete(self, result: Optional[Dict] = None, confidence: float = 0.0):
        self.status = "completed"
        self.result = result
        self.confidence = confidence
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def fail(self):
        self.status = "failed"

    def skip(self):
        self.status = "skipped"

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id, "name": self.name,
            "description": self.description, "module": self.module,
            "priority": self.priority, "status": self.status,
            "estimated_time_min": self.estimated_time_min,
            "estimated_api_calls": self.estimated_api_calls,
            "estimated_memory_mb": self.estimated_memory_mb,
            "dependencies": self.dependencies,
            "confidence": self.confidence,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class ResearchPlan:
    """A complete research plan."""

    __slots__ = (
        "plan_id", "topic", "goal_title", "niche",
        "tasks", "status", "overall_confidence",
        "total_estimated_time_min", "total_estimated_api_calls",
        "total_estimated_memory_mb", "expected_cost_usd",
        "created_at", "updated_at", "completed_at",
        "metadata",
    )

    STATUSES = ["draft", "ready", "running", "completed", "failed", "cancelled"]

    def __init__(self, topic: str, goal_title: str = "", niche: str = "general"):
        self.plan_id = f"plan_{int(datetime.now(timezone.utc).timestamp())}_{hash(topic) % 100000}"
        self.topic = topic
        self.goal_title = goal_title or f"Research {topic}"
        self.niche = niche
        self.tasks: List[PlanTask] = []
        self.status = "draft"
        self.overall_confidence = 0.0
        self.total_estimated_time_min = 0.0
        self.total_estimated_api_calls = 0
        self.total_estimated_memory_mb = 0.0
        self.expected_cost_usd = 0.0
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.completed_at = ""
        self.metadata: Dict = {}

    def add_task(self, task: PlanTask):
        self.tasks.append(task)
        self._recalculate_totals()

    def remove_task(self, task_id: str) -> bool:
        for i, t in enumerate(self.tasks):
            if t.task_id == task_id:
                self.tasks.pop(i)
                self._recalculate_totals()
                return True
        return False

    def get_task(self, task_id: str) -> Optional[PlanTask]:
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    def get_ready_tasks(self) -> List[PlanTask]:
        """Get tasks whose dependencies are all completed."""
        completed_ids = {t.task_id for t in self.tasks if t.status == "completed"}
        ready = []
        for task in self.tasks:
            if task.status != "pending":
                continue
            deps_met = all(dep_id in completed_ids for dep_id in task.dependencies)
            if deps_met:
                ready.append(task)
        return ready

    def get_critical_path(self) -> List[PlanTask]:
        """Get the critical path (longest dependency chain)."""
        # Simple: sort by dependency depth then priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "BACKGROUND": 4}
        return sorted(self.tasks, key=lambda t: (len(t.dependencies), priority_order.get(t.priority, 5)))

    def _recalculate_totals(self):
        self.total_estimated_time_min = sum(t.estimated_time_min for t in self.tasks)
        self.total_estimated_api_calls = sum(t.estimated_api_calls for t in self.tasks)
        self.total_estimated_memory_mb = max((t.estimated_memory_mb for t in self.tasks), default=0.0)
        self.expected_cost_usd = round(self.total_estimated_api_calls * 0.002, 4)

    def get_progress(self) -> float:
        """Get completion progress (0.0 to 1.0)."""
        if not self.tasks:
            return 0.0
        completed = sum(1 for t in self.tasks if t.status in ("completed", "skipped"))
        return round(completed / len(self.tasks), 3)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id, "topic": self.topic,
            "goal_title": self.goal_title, "niche": self.niche,
            "tasks": [t.to_dict() for t in self.tasks],
            "status": self.status,
            "overall_confidence": self.overall_confidence,
            "total_estimated_time_min": self.total_estimated_time_min,
            "total_estimated_api_calls": self.total_estimated_api_calls,
            "total_estimated_memory_mb": self.total_estimated_memory_mb,
            "expected_cost_usd": self.expected_cost_usd,
            "progress": self.get_progress(),
            "created_at": self.created_at, "updated_at": self.updated_at,
            "completed_at": self.completed_at, "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchPlan":
        p = cls(topic=data.get("topic", ""), goal_title=data.get("goal_title", ""),
                niche=data.get("niche", "general"))
        p.plan_id = data.get("plan_id", p.plan_id)
        p.status = data.get("status", "draft")
        p.overall_confidence = data.get("overall_confidence", 0.0)
        for td in data.get("tasks", []):
            task = PlanTask(
                name=td.get("name", ""), description=td.get("description", ""),
                module=td.get("module", ""), priority=td.get("priority", "MEDIUM"),
                estimated_time_min=td.get("estimated_time_min", 5.0),
                estimated_api_calls=td.get("estimated_api_calls", 0),
                estimated_memory_mb=td.get("estimated_memory_mb", 10.0),
                dependencies=td.get("dependencies", []),
            )
            task.task_id = td.get("task_id", task.task_id)
            task.status = td.get("status", "pending")
            task.confidence = td.get("confidence", 0.0)
            p.tasks.append(task)
        p.created_at = data.get("created_at", p.created_at)
        p.updated_at = data.get("updated_at", p.updated_at)
        p.completed_at = data.get("completed_at", "")
        p.metadata = data.get("metadata", {})
        p._recalculate_totals()
        return p
