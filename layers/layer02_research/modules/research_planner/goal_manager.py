"""
Goal Manager
Layer 2: Research Engine — Module 9

Manages research goals:
- Goal creation and tracking
- Goal hierarchies (parent/child)
- Goal status management
- Goal scoring
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional


class ResearchGoal:
    """A research goal."""

    __slots__ = (
        "goal_id", "title", "description", "topic", "niche",
        "priority", "status", "parent_goal_id",
        "target_confidence", "actual_confidence",
        "created_at", "updated_at", "completed_at",
        "metadata",
    )

    PRIORITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    STATUSES = ["pending", "in_progress", "completed", "failed", "cancelled"]

    def __init__(
        self,
        title: str,
        description: str = "",
        topic: str = "",
        niche: str = "general",
        priority: str = "MEDIUM",
        target_confidence: float = 0.8,
        parent_goal_id: str = "",
    ):
        self.goal_id = f"goal_{int(datetime.now(timezone.utc).timestamp())}_{hash(title) % 100000}"
        self.title = title
        self.description = description
        self.topic = topic
        self.niche = niche
        self.priority = priority if priority in self.PRIORITIES else "MEDIUM"
        self.status = "pending"
        self.parent_goal_id = parent_goal_id
        self.target_confidence = max(0.0, min(1.0, target_confidence))
        self.actual_confidence = 0.0
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.completed_at = ""
        self.metadata: Dict = {}

    def complete(self, confidence: float = 0.0):
        self.status = "completed"
        self.actual_confidence = max(0.0, min(1.0, confidence))
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.completed_at

    def fail(self):
        self.status = "failed"
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def cancel(self):
        self.status = "cancelled"
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def is_achieved(self) -> bool:
        return self.status == "completed" and self.actual_confidence >= self.target_confidence

    def to_dict(self) -> dict:
        return {
            "goal_id": self.goal_id, "title": self.title,
            "description": self.description, "topic": self.topic,
            "niche": self.niche, "priority": self.priority,
            "status": self.status, "parent_goal_id": self.parent_goal_id,
            "target_confidence": self.target_confidence,
            "actual_confidence": self.actual_confidence,
            "is_achieved": self.is_achieved(),
            "created_at": self.created_at, "updated_at": self.updated_at,
            "completed_at": self.completed_at, "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchGoal":
        g = cls(
            title=data.get("title", ""), description=data.get("description", ""),
            topic=data.get("topic", ""), niche=data.get("niche", "general"),
            priority=data.get("priority", "MEDIUM"),
            target_confidence=data.get("target_confidence", 0.8),
            parent_goal_id=data.get("parent_goal_id", ""),
        )
        g.goal_id = data.get("goal_id", g.goal_id)
        g.status = data.get("status", "pending")
        g.actual_confidence = data.get("actual_confidence", 0.0)
        g.created_at = data.get("created_at", g.created_at)
        g.updated_at = data.get("updated_at", g.updated_at)
        g.completed_at = data.get("completed_at", "")
        g.metadata = data.get("metadata", {})
        return g


class GoalManager:
    """Manages research goals."""

    def __init__(self):
        self._goals: Dict[str, ResearchGoal] = {}

    def create_goal(self, title: str, **kwargs) -> ResearchGoal:
        goal = ResearchGoal(title, **kwargs)
        self._goals[goal.goal_id] = goal
        return goal

    def get_goal(self, goal_id: str) -> Optional[ResearchGoal]:
        return self._goals.get(goal_id)

    def update_goal(self, goal_id: str, **kwargs) -> Optional[ResearchGoal]:
        goal = self._goals.get(goal_id)
        if not goal:
            return None
        for key, val in kwargs.items():
            if hasattr(goal, key):
                setattr(goal, key, val)
        goal.updated_at = datetime.now(timezone.utc).isoformat()
        return goal

    def complete_goal(self, goal_id: str, confidence: float = 0.0) -> bool:
        goal = self._goals.get(goal_id)
        if goal:
            goal.complete(confidence)
            return True
        return False

    def list_goals(self, status: Optional[str] = None, priority: Optional[str] = None) -> List[ResearchGoal]:
        goals = list(self._goals.values())
        if status:
            goals = [g for g in goals if g.status == status]
        if priority:
            goals = [g for g in goals if g.priority == priority]
        return goals

    def get_pending(self) -> List[ResearchGoal]:
        return self.list_goals(status="pending")

    def get_achieved(self) -> List[ResearchGoal]:
        return [g for g in self._goals.values() if g.is_achieved()]

    def get_by_topic(self, topic: str) -> List[ResearchGoal]:
        return [g for g in self._goals.values() if g.topic == topic]

    def size(self) -> int:
        return len(self._goals)
