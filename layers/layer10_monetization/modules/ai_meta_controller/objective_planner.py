"""Objective Planner — Convert goals into tasks."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_OP_COUNTER = itertools.count(1)


class ObjectivePlan:
    """A plan to achieve an objective."""

    __slots__ = ("plan_id", "goal_id", "steps", "current_step",
                 "status", "created_at")

    def __init__(self, goal_id: str = "") -> None:
        self.plan_id: str = f"plan_{next(_OP_COUNTER)}"
        self.goal_id = goal_id
        self.steps: List[Dict[str, Any]] = []
        self.current_step: int = 0
        self.status: str = "created"
        self.created_at: float = time.time()

    def add_step(self, layer: str, action: str, description: str = "") -> Dict[str, Any]:
        step = {"order": len(self.steps), "layer": layer, "action": action,
                "description": description, "status": "pending"}
        self.steps.append(step)
        return step

    @property
    def is_complete(self) -> bool:
        return all(s["status"] in ("completed", "skipped") for s in self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id, "goal_id": self.goal_id,
            "total_steps": len(self.steps), "current_step": self.current_step,
            "status": self.status,
        }


class ObjectivePlanner:
    """Convert large goals into executable task plans."""

    DEFAULT_PLANS = {
        "grow_followers": [
            ("layer02_research", "trend_analysis", "Research trending topics"),
            ("layer03_intelligence", "content_understanding", "Analyze audience"),
            ("layer04_writing", "draft", "Write engaging content"),
            ("layer05_image", "image_plan", "Create visuals"),
            ("layer06_quality", "quality_check", "Quality assurance"),
            ("layer07_publishing", "publish", "Publish content"),
            ("layer08_analytics", "analytics", "Track performance"),
            ("layer09_learning", "learn", "Learn from results"),
        ],
        "increase_engagement": [
            ("layer02_research", "trend_analysis", "Research engagement patterns"),
            ("layer04_writing", "draft", "Write interactive content"),
            ("layer06_quality", "quality_check", "Quality check"),
            ("layer07_publishing", "publish", "Publish"),
            ("layer08_analytics", "analytics", "Analyze engagement"),
            ("layer09_learning", "learn", "Optimize for engagement"),
        ],
    }

    def __init__(self) -> None:
        self._plans: List[ObjectivePlan] = []

    def create_plan(self, goal_id: str, goal_type: str = "",
                    custom_steps: Optional[List[Dict[str, str]]] = None) -> ObjectivePlan:
        plan = ObjectivePlan(goal_id)
        steps = custom_steps or self.DEFAULT_PLANS.get(goal_type, [])
        for step in steps:
            if isinstance(step, tuple) and len(step) >= 2:
                plan.add_step(step[0], step[1], step[2] if len(step) > 2 else "")
            elif isinstance(step, dict):
                plan.add_step(step.get("layer", ""), step.get("action", ""), step.get("description", ""))
        self._plans.append(plan)
        return plan

    def get_plan(self, plan_id: str) -> Optional[ObjectivePlan]:
        for p in self._plans:
            if p.plan_id == plan_id:
                return p
        return None

    def get_plans_for_goal(self, goal_id: str) -> List[ObjectivePlan]:
        return [p for p in self._plans if p.goal_id == goal_id]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_plans": len(self._plans), "completed": sum(1 for p in self._plans if p.is_complete)}
