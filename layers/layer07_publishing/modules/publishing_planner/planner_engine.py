"""Planner Engine — Core orchestrator for publishing planning."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.publishing_planner.publish_plan import PublishPlan
from layers.layer07_publishing.modules.publishing_planner.platform_selector import PlatformSelector
from layers.layer07_publishing.modules.publishing_planner.scheduler import Scheduler

_COUNTER = itertools.count(1)


class PlannerEngine:
    """Orchestrate publishing plan creation."""

    def __init__(
        self,
        selector: Optional[PlatformSelector] = None,
        scheduler: Optional[Scheduler] = None,
    ) -> None:
        self.selector = selector or PlatformSelector()
        self.scheduler = scheduler or Scheduler()
        self._plan_count = 0

    def create_plan(
        self,
        content_id: str,
        content_type: str = "post",
        preferred_platforms: Optional[List[str]] = None,
        max_platforms: int = 5,
        schedule_mode: str = "optimal",  # immediate, optimal, delayed, stagger
        delay_seconds: float = 3600,
    ) -> PublishPlan:
        """Create a complete publishing plan."""
        plan = PublishPlan(
            plan_id=f"pp_{next(_COUNTER)}",
            content_id=content_id,
        )

        # 1. Select platforms
        targets = self.selector.select(
            content_type=content_type,
            preferred_platforms=preferred_platforms,
            max_platforms=max_platforms,
        )

        for target in targets:
            plan.add_target(target)

        # 2. Schedule
        if schedule_mode == "immediate":
            self.scheduler.schedule_immediate(plan)
        elif schedule_mode == "optimal":
            self.scheduler.schedule_optimal(plan)
        elif schedule_mode == "delayed":
            self.scheduler.schedule_delayed(plan, delay_seconds)
        elif schedule_mode == "stagger":
            self.scheduler.stagger(plan)

        # 3. Set priority based on engagement estimates
        if plan.targets:
            max_engagement = max(t.estimated_engagement for t in plan.targets)
            plan.overall_priority = max(1, int((1 - max_engagement) * 10))

        plan.metadata = {
            "content_type": content_type,
            "schedule_mode": schedule_mode,
            "platform_count": len(plan.targets),
        }

        self._plan_count += 1
        return plan

    def create_quick_plan(self, content_id: str, platforms: List[str]) -> PublishPlan:
        """Quick plan with immediate publishing to specific platforms."""
        plan = self.create_plan(
            content_id=content_id,
            content_type="post",
            preferred_platforms=platforms,
            max_platforms=len(platforms),
            schedule_mode="immediate",
        )
        return plan

    def get_plan_summary(self, plan: PublishPlan) -> Dict[str, Any]:
        """Get summary of a publishing plan."""
        return {
            "plan_id": plan.plan_id,
            "platforms": plan.get_platforms(),
            "platform_count": len(plan.targets),
            "priority": plan.overall_priority,
            "scheduled": self.scheduler.get_scheduled(plan),
        }

    @property
    def plan_count(self) -> int:
        return self._plan_count
