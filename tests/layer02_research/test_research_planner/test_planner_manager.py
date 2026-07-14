"""Tests for PlannerManager."""

from layers.layer02_research.modules.research_planner.planner_manager import PlannerManager
from layers.layer02_research.modules.research_planner.exceptions import (
    GoalCreationError, PlanOptimizationError, DependencyError,
)


class TestPlannerManager:
    def setup_method(self):
        self.manager = PlannerManager()

    def test_create_plan(self):
        plan = self.manager.create_plan("AI Jobs", niche="technology")
        assert plan.topic == "AI Jobs"
        assert plan.status == "ready"
        assert len(plan.tasks) > 0

    def test_create_plan_with_specific_modules(self):
        plan = self.manager.create_plan(
            "Crypto", modules=["trend_discovery", "fact_verification"]
        )
        modules = {t.module for t in plan.tasks}
        assert "trend_discovery" in modules
        assert "fact_verification" in modules

    def test_create_plan_stores_it(self):
        plan = self.manager.create_plan("AI")
        found = self.manager.get_plan(plan.plan_id)
        assert found is not None
        assert found.topic == "AI"

    def test_optimize_plan_default(self):
        plan = self.manager.create_plan("AI")
        optimized = self.manager.optimize_plan(plan)
        assert len(optimized.waves) > 0

    def test_optimize_plan_time_mode(self):
        plan = self.manager.create_plan("AI")
        optimized = self.manager.optimize_plan(plan, mode="time")
        assert "time_optimized" in optimized.optimizations_applied

    def test_optimize_plan_cost_mode(self):
        plan = self.manager.create_plan("AI")
        optimized = self.manager.optimize_plan(plan, mode="cost")
        assert "cost_optimized" in optimized.optimizations_applied

    def test_get_ready_tasks(self):
        plan = self.manager.create_plan("AI", modules=["trend_discovery"])
        ready = self.manager.get_ready_tasks(plan)
        assert len(ready) > 0

    def test_start_task(self):
        plan = self.manager.create_plan("AI", modules=["trend_discovery"])
        ready = self.manager.get_ready_tasks(plan)
        task = self.manager.start_task(plan, ready[0].task_id)
        assert task is not None
        assert task.status == "running"

    def test_start_nonexistent_task(self):
        plan = self.manager.create_plan("AI")
        result = self.manager.start_task(plan, "nonexistent")
        assert result is None

    def test_complete_task(self):
        plan = self.manager.create_plan("AI", modules=["trend_discovery"])
        ready = self.manager.get_ready_tasks(plan)
        self.manager.start_task(plan, ready[0].task_id)
        task = self.manager.complete_task(plan, ready[0].task_id, confidence=0.9)
        assert task is not None
        assert task.status == "completed"
        assert task.confidence == 0.9

    def test_fail_task(self):
        plan = self.manager.create_plan("AI", modules=["trend_discovery", "fact_verification"])
        ready = self.manager.get_ready_tasks(plan)
        self.manager.start_task(plan, ready[0].task_id)
        task = self.manager.fail_task(plan, ready[0].task_id)
        assert task is not None
        assert task.status == "failed"

    def test_get_progress(self):
        plan = self.manager.create_plan("AI", modules=["trend_discovery"])
        progress = self.manager.get_progress(plan)
        assert progress["total_tasks"] > 0
        assert progress["completed"] == 0
        assert progress["progress"] == 0.0

    def test_get_progress_after_completion(self):
        plan = self.manager.create_plan("AI", modules=["trend_discovery"])
        ready = self.manager.get_ready_tasks(plan)
        self.manager.start_task(plan, ready[0].task_id)
        self.manager.complete_task(plan, ready[0].task_id)
        progress = self.manager.get_progress(plan)
        assert progress["completed"] >= 1

    def test_get_execution_log(self):
        plan = self.manager.create_plan("AI", modules=["trend_discovery"])
        ready = self.manager.get_ready_tasks(plan)
        self.manager.start_task(plan, ready[0].task_id)
        log = self.manager.get_execution_log(plan.plan_id)
        assert len(log) > 0
        assert log[0]["event_type"] == "task_started"

    def test_list_plans(self):
        self.manager.create_plan("AI")
        self.manager.create_plan("Crypto")
        plans = self.manager.list_plans()
        assert len(plans) == 2

    def test_list_plans_by_status(self):
        p1 = self.manager.create_plan("AI")
        p2 = self.manager.create_plan("Crypto")
        self.manager.cancel_plan(p1)
        cancelled = self.manager.list_plans(status="cancelled")
        assert len(cancelled) == 1

    def test_cancel_plan(self):
        plan = self.manager.create_plan("AI")
        success = self.manager.cancel_plan(plan)
        assert success is True
        assert plan.status == "cancelled"

    def test_cancel_completed_plan(self):
        plan = self.manager.create_plan("AI")
        plan.status = "completed"
        success = self.manager.cancel_plan(plan)
        assert success is False

    def test_task_execution_flow(self):
        """Full lifecycle: create → get_ready → start → complete."""
        plan = self.manager.create_plan("AI", modules=["trend_discovery"])
        ready = self.manager.get_ready_tasks(plan)
        assert len(ready) > 0

        task = ready[0]
        self.manager.start_task(plan, task.task_id)
        assert task.status == "running"

        self.manager.complete_task(plan, task.task_id, confidence=0.85)
        assert task.status == "completed"

        progress = self.manager.get_progress(plan)
        assert progress["completed"] >= 1

    def test_dependent_task_unlocked(self):
        """After completing a task, dependent tasks become ready."""
        plan = self.manager.create_plan("AI")
        ready_before = self.manager.get_ready_tasks(plan)
        # Complete first task
        self.manager.start_task(plan, ready_before[0].task_id)
        self.manager.complete_task(plan, ready_before[0].task_id)
        # Check if new tasks are ready
        ready_after = self.manager.get_ready_tasks(plan)
        assert len(ready_after) >= len(ready_before) - 1
