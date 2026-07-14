"""
Planner Manager
Layer 2: Research Engine — Module 9

Central orchestrator for research planning:
- Creates research plans from goals
- Decomposes goals into tasks
- Manages dependencies and priorities
- Optimizes and validates plans
- Tracks execution progress
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from layers.layer02_research.modules.research_planner.goal_manager import GoalManager
from layers.layer02_research.modules.research_planner.research_plan import PlanTask, ResearchPlan
from layers.layer02_research.modules.research_planner.task_decomposer import TaskDecomposer
from layers.layer02_research.modules.research_planner.dependency_graph import DependencyGraph
from layers.layer02_research.modules.research_planner.priority_engine import PriorityEngine
from layers.layer02_research.modules.research_planner.resource_estimator import ResourceEstimator
from layers.layer02_research.modules.research_planner.plan_optimizer import PlanOptimizer, OptimizedPlan
from layers.layer02_research.modules.research_planner.exceptions import (
    GoalCreationError, PlanOptimizationError, DependencyError,
)


class PlannerManager:
    """
    Central manager for research planning.

    Usage:
        planner = PlannerManager()
        plan = planner.create_plan(topic="AI Jobs", niche="technology")
        opt = planner.optimize_plan(plan)
        ready = planner.get_ready_tasks(plan)
    """

    def __init__(self):
        self.goal_manager = GoalManager()
        self.decomposer = TaskDecomposer()
        self.priority_engine = PriorityEngine()
        self.resource_estimator = ResourceEstimator()
        self.plan_optimizer = PlanOptimizer()
        self._plans: Dict[str, ResearchPlan] = {}
        self._execution_log: List[Dict] = []

    def create_plan(
        self,
        topic: str,
        goal_title: str = "",
        niche: str = "general",
        modules: Optional[List[str]] = None,
        custom_tasks: Optional[List[Dict]] = None,
        target_confidence: float = 0.8,
    ) -> ResearchPlan:
        """Create a complete research plan for a topic."""
        try:
            # Create goal
            goal = self.goal_manager.create_goal(
                title=goal_title or f"Research {topic}",
                topic=topic,
                niche=niche,
                target_confidence=target_confidence,
            )

            # Decompose into tasks
            tasks = self.decomposer.decompose(topic, modules=modules, custom_tasks=custom_tasks)

            # Build plan
            plan = ResearchPlan(topic=topic, goal_title=goal.title, niche=niche)
            for task in tasks:
                plan.add_task(task)

            # Set goal reference
            plan.metadata["goal_id"] = goal.goal_id

            # Assign priorities
            self.priority_engine.assign_priorities(plan.tasks)

            # Validate dependencies
            self._validate_plan(plan)

            # Estimate resources
            est = self.resource_estimator.estimate_plan(plan)
            plan.total_estimated_time_min = est.estimated_time_min
            plan.total_estimated_api_calls = est.estimated_api_calls
            plan.total_estimated_memory_mb = est.estimated_memory_mb
            plan.expected_cost_usd = est.estimated_cost_usd

            plan.overall_confidence = est.expected_confidence
            plan.status = "ready"
            self._plans[plan.plan_id] = plan

            return plan

        except Exception as exc:
            raise GoalCreationError(f"Failed to create plan: {exc}") from exc

    def optimize_plan(self, plan: ResearchPlan, mode: str = "balanced") -> OptimizedPlan:
        """Optimize a plan for execution."""
        try:
            if mode == "time":
                return self.plan_optimizer.optimize_for_time(plan)
            elif mode == "cost":
                return self.plan_optimizer.optimize_for_cost(plan)
            return self.plan_optimizer.optimize(plan)
        except Exception as exc:
            raise PlanOptimizationError(f"Failed to optimize plan: {exc}") from exc

    def get_ready_tasks(self, plan: ResearchPlan) -> List[PlanTask]:
        """Get tasks that are ready to execute."""
        return plan.get_ready_tasks()

    def start_task(self, plan: ResearchPlan, task_id: str) -> Optional[PlanTask]:
        """Mark a task as started."""
        task = plan.get_task(task_id)
        if not task:
            return None
        task.start()
        self._log_event(plan.plan_id, "task_started", {"task_id": task_id})
        return task

    def complete_task(
        self, plan: ResearchPlan, task_id: str,
        result: Optional[Dict] = None, confidence: float = 0.0,
    ) -> Optional[PlanTask]:
        """Mark a task as completed."""
        task = plan.get_task(task_id)
        if not task:
            return None
        task.complete(result=result, confidence=confidence)
        self._log_event(plan.plan_id, "task_completed", {
            "task_id": task_id, "confidence": confidence,
        })
        return task

    def fail_task(self, plan: ResearchPlan, task_id: str) -> Optional[PlanTask]:
        """Mark a task as failed and boost dependent task priorities."""
        task = plan.get_task(task_id)
        if not task:
            return None
        task.fail()
        self.priority_engine.adjust_for_failure(plan.tasks, task_id)
        self._log_event(plan.plan_id, "task_failed", {"task_id": task_id})
        return task

    def get_progress(self, plan: ResearchPlan) -> Dict:
        """Get plan execution progress."""
        total = len(plan.tasks)
        completed = sum(1 for t in plan.tasks if t.status == "completed")
        failed = sum(1 for t in plan.tasks if t.status == "failed")
        running = sum(1 for t in plan.tasks if t.status == "running")
        pending = sum(1 for t in plan.tasks if t.status == "pending")

        return {
            "plan_id": plan.plan_id,
            "topic": plan.topic,
            "status": plan.status,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "progress": plan.get_progress(),
            "elapsed_tasks": completed + failed,
        }

    def get_execution_log(self, plan_id: str) -> List[Dict]:
        """Get execution log for a plan."""
        return [e for e in self._execution_log if e.get("plan_id") == plan_id]

    def get_plan(self, plan_id: str) -> Optional[ResearchPlan]:
        """Get a plan by ID."""
        return self._plans.get(plan_id)

    def list_plans(self, status: Optional[str] = None) -> List[ResearchPlan]:
        """List all plans, optionally filtered by status."""
        plans = list(self._plans.values())
        if status:
            plans = [p for p in plans if p.status == status]
        return plans

    def cancel_plan(self, plan: ResearchPlan) -> bool:
        """Cancel a plan and mark incomplete tasks."""
        if plan.status in ("completed", "cancelled"):
            return False
        plan.status = "cancelled"
        for task in plan.tasks:
            if task.status in ("pending", "running"):
                task.skip()
        self._log_event(plan.plan_id, "plan_cancelled", {})
        return True

    def _validate_plan(self, plan: ResearchPlan):
        """Validate plan dependencies have no cycles."""
        graph = DependencyGraph()
        for task in plan.tasks:
            graph.add_node(task.task_id)
        for task in plan.tasks:
            for dep_id in task.dependencies:
                graph.add_edge(dep_id, task.task_id)

        if graph.has_cycle():
            raise DependencyError(
                f"Cyclic dependency detected in plan '{plan.topic}'"
            )

    def _log_event(self, plan_id: str, event_type: str, data: Dict):
        """Log a planning event."""
        self._execution_log.append({
            "plan_id": plan_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        })
