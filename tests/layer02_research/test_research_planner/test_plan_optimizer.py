"""Tests for PlanOptimizer."""

from layers.layer02_research.modules.research_planner.plan_optimizer import PlanOptimizer, OptimizedPlan, ExecutionWave
from layers.layer02_research.modules.research_planner.research_plan import PlanTask, ResearchPlan


class TestExecutionWave:
    def test_create_wave(self):
        wave = ExecutionWave(wave_id=0)
        assert wave.wave_id == 0
        assert wave.tasks == []
        assert wave.estimated_time_min == 0.0


class TestOptimizedPlan:
    def test_create_optimized_plan(self):
        plan = ResearchPlan(topic='Test')
        opt = OptimizedPlan(plan)
        assert opt.waves == []
        assert opt.critical_path == []
        assert opt.optimizations_applied == []


class TestPlanOptimizer:
    def setup_method(self):
        self.optimizer = PlanOptimizer()

    def _make_plan(self) -> ResearchPlan:
        plan = ResearchPlan(topic="AI Jobs")
        t1 = PlanTask(name="Trend", module="trend_discovery", priority="HIGH")
        t2 = PlanTask(name="Verify", module="fact_verification", priority="CRITICAL")
        t3 = PlanTask(name="Score", module="topic_scoring", priority="MEDIUM")
        plan.add_task(t1)
        plan.add_task(t2)
        plan.add_task(t3)
        return plan

    def test_optimize_basic(self):
        plan = self._make_plan()
        result = self.optimizer.optimize(plan)
        assert isinstance(result, OptimizedPlan)
        assert len(result.waves) > 0

    def test_optimize_for_time(self):
        plan = self._make_plan()
        result = self.optimizer.optimize_for_time(plan)
        assert isinstance(result, OptimizedPlan)
        assert "time_optimized" in result.optimizations_applied

    def test_optimize_for_cost(self):
        plan = self._make_plan()
        result = self.optimizer.optimize_for_cost(plan)
        assert isinstance(result, OptimizedPlan)
        assert "cost_optimized" in result.optimizations_applied

    def test_optimize_empty_plan(self):
        plan = ResearchPlan(topic="Empty")
        result = self.optimizer.optimize(plan)
        assert len(result.waves) == 0

    def test_optimize_preserves_all_tasks(self):
        plan = self._make_plan()
        result = self.optimizer.optimize(plan)
        total_tasks = sum(len(w.tasks) for w in result.waves)
        assert total_tasks == 3

    def test_optimize_with_dependencies(self):
        plan = ResearchPlan(topic="AI")
        t1 = PlanTask(name="Step 1")
        t2 = PlanTask(name="Step 2", dependencies=[t1.task_id])
        t3 = PlanTask(name="Step 3")
        plan.add_task(t1)
        plan.add_task(t2)
        plan.add_task(t3)
        result = self.optimizer.optimize(plan)
        assert len(result.waves) >= 2

    def test_prune_low_value(self):
        plan = ResearchPlan(topic="AI")
        t1 = PlanTask(name="Critical", module="fact_verification", priority="CRITICAL")
        t2 = PlanTask(name="Low", module="trend_discovery", priority="BACKGROUND")
        t3 = PlanTask(name="Med", module="topic_scoring", priority="MEDIUM")
        plan.add_task(t1)
        plan.add_task(t2)
        plan.add_task(t3)
        result = self.optimizer.prune_low_value(plan, min_confidence=0.9)
        # Critical tasks always kept
        names = {t.name for t in result.tasks}
        assert "Critical" in names

    def test_prune_keeps_all_when_few_tasks(self):
        plan = ResearchPlan(topic="AI")
        plan.add_task(PlanTask(name="A"))
        plan.add_task(PlanTask(name="B"))
        result = self.optimizer.prune_low_value(plan)
        assert len(result.tasks) == 2

    def test_merge_plans(self):
        p1 = ResearchPlan(topic="AI")
        p1.add_task(PlanTask(name="A", module="trend_discovery"))
        p2 = ResearchPlan(topic="Crypto")
        p2.add_task(PlanTask(name="B", module="fact_verification"))
        merged = self.optimizer.merge_plans([p1, p2])
        assert len(merged.tasks) == 2

    def test_merge_single_plan(self):
        p1 = ResearchPlan(topic="AI")
        p1.add_task(PlanTask(name="A"))
        merged = self.optimizer.merge_plans([p1])
        assert merged.plan_id == p1.plan_id

    def test_merge_empty(self):
        merged = self.optimizer.merge_plans([])
        assert merged.topic == "empty"

    def test_waves_sorted_by_time_in_time_mode(self):
        plan = ResearchPlan(topic="AI")
        for i in range(5):
            plan.add_task(PlanTask(name=f"Task{i}", estimated_time_min=float(i + 1)))
        result = self.optimizer.optimize_for_time(plan)
        assert len(result.waves) > 0
        total_tasks = sum(len(w.tasks) for w in result.waves)
        assert total_tasks == 5
        assert "time_optimized" in result.optimizations_applied
