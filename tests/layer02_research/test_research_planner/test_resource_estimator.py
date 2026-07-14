"""Tests for ResourceEstimator."""

from layers.layer02_research.modules.research_planner.resource_estimator import ResourceEstimator, ResourceEstimate
from layers.layer02_research.modules.research_planner.research_plan import PlanTask, ResearchPlan


class TestResourceEstimate:
    def test_to_dict(self):
        est = ResourceEstimate()
        est.estimated_time_min = 10.5
        est.estimated_api_calls = 5
        est.estimated_cost_usd = 0.01
        d = est.to_dict()
        assert d["estimated_time_min"] == 10.5
        assert d["estimated_api_calls"] == 5
        assert d["estimated_cost_usd"] == 0.01


class TestResourceEstimator:
    def setup_method(self):
        self.estimator = ResourceEstimator()

    def test_estimate_task(self):
        task = PlanTask(
            name="Test",
            module="trend_discovery",
            estimated_time_min=5.0,
            estimated_api_calls=3,
            estimated_memory_mb=20.0,
        )
        est = self.estimator.estimate_task(task)
        assert est.estimated_time_min > 0
        assert est.estimated_api_calls == 3
        assert est.estimated_memory_mb >= 20.0

    def test_estimate_task_cost(self):
        task = PlanTask(name="Test", module="fact_verification", estimated_api_calls=10)
        est = self.estimator.estimate_task(task)
        assert est.estimated_cost_usd > 0

    def test_estimate_task_confidence(self):
        task = PlanTask(name="Test", module="fact_verification")
        est = self.estimator.estimate_task(task)
        assert est.expected_confidence > 0.8

    def test_estimate_task_unknown_module(self):
        task = PlanTask(name="Test", module="unknown")
        est = self.estimator.estimate_task(task)
        assert est.estimated_memory_mb > 0

    def test_estimate_plan(self):
        plan = ResearchPlan(topic="AI")
        plan.add_task(PlanTask(name="A", module="trend_discovery", estimated_api_calls=2))
        plan.add_task(PlanTask(name="B", module="fact_verification", estimated_api_calls=3))
        est = self.estimator.estimate_plan(plan)
        assert est.estimated_api_calls == 5
        assert est.estimated_cost_usd > 0

    def test_estimate_plan_memory_is_max(self):
        plan = ResearchPlan(topic="AI")
        plan.add_task(PlanTask(name="A", module="trend_discovery", estimated_memory_mb=10))
        plan.add_task(PlanTask(name="B", module="knowledge_collector", estimated_memory_mb=50))
        est = self.estimator.estimate_plan(plan)
        assert est.estimated_memory_mb >= 50.0

    def test_estimate_plan_empty(self):
        plan = ResearchPlan(topic="AI")
        est = self.estimator.estimate_plan(plan)
        assert est.estimated_time_min == 0.0
        assert est.estimated_api_calls == 0
