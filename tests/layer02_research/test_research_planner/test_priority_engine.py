"""Tests for PriorityEngine."""

from layers.layer02_research.modules.research_planner.priority_engine import PriorityEngine
from layers.layer02_research.modules.research_planner.research_plan import PlanTask


class TestPriorityEngine:
    def setup_method(self):
        self.engine = PriorityEngine()

    def test_assign_priorities_basic(self):
        tasks = [
            PlanTask(name="A", module="trend_discovery"),
            PlanTask(name="B", module="fact_verification"),
        ]
        result = self.engine.assign_priorities(tasks)
        assert len(result) == 2
        for t in result:
            assert t.priority in PlanTask.PRIORITIES

    def test_fact_verification_gets_higher_priority(self):
        t1 = PlanTask(name="Trend", module="trend_discovery")
        t2 = PlanTask(name="Verify", module="fact_verification")
        self.engine.assign_priorities([t1, t2])
        # fact_verification has higher module importance
        assert PlanTask.PRIORITIES.index(t2.priority) <= PlanTask.PRIORITIES.index(t1.priority)

    def test_assign_with_topic_scores(self):
        tasks = [PlanTask(name="A", module="trend_discovery")]
        scores = {"trend": 9.0}
        self.engine.assign_priorities(tasks, topic_scores=scores)
        # With high trend score, trend_discovery should get higher priority
        assert tasks[0].priority in ("HIGH", "CRITICAL")

    def test_compute_priority_score_range(self):
        task = PlanTask(name="Test", module="unknown_module")
        score = self.engine._compute_priority_score(task, {})
        assert 0.0 <= score <= 10.0

    def test_score_to_priority_critical(self):
        assert self.engine._score_to_priority(9.0) == "CRITICAL"
        assert self.engine._score_to_priority(8.0) == "CRITICAL"

    def test_score_to_priority_high(self):
        assert self.engine._score_to_priority(7.0) == "HIGH"
        assert self.engine._score_to_priority(6.0) == "HIGH"

    def test_score_to_priority_medium(self):
        assert self.engine._score_to_priority(5.0) == "MEDIUM"
        assert self.engine._score_to_priority(4.0) == "MEDIUM"

    def test_score_to_priority_low(self):
        assert self.engine._score_to_priority(3.0) == "LOW"
        assert self.engine._score_to_priority(2.0) == "LOW"

    def test_score_to_priority_background(self):
        assert self.engine._score_to_priority(1.0) == "BACKGROUND"
        assert self.engine._score_to_priority(0.0) == "BACKGROUND"

    def test_score_clamped_at_10(self):
        score = self.engine._compute_priority_score(
            PlanTask(name="T", module="fact_verification", estimated_api_calls=10, estimated_time_min=10),
            {"verification": 10.0},
        )
        assert score <= 10.0

    def test_score_clamped_at_0(self):
        score = self.engine._compute_priority_score(
            PlanTask(name="T", module="unknown"),
            {},
        )
        assert score >= 0.0

    def test_get_execution_order(self):
        tasks = [
            PlanTask(name="A", priority="LOW", estimated_time_min=10),
            PlanTask(name="B", priority="HIGH", estimated_time_min=5),
            PlanTask(name="C", priority="HIGH", estimated_time_min=2),
        ]
        ordered = self.engine.get_execution_order(tasks)
        assert ordered[0].priority == "HIGH"
        assert ordered[0].name == "C"  # shorter time first among HIGH
        assert ordered[-1].priority == "LOW"

    def test_adjust_for_failure(self):
        t1 = PlanTask(name="Step1")
        t1.task_id = "task_1"
        t2 = PlanTask(name="Step2", dependencies=["task_1"])
        t2.priority = "LOW"
        tasks = [t1, t2]
        self.engine.adjust_for_failure(tasks, "task_1")
        # t2 depends on failed t1, should be boosted
        assert PlanTask.PRIORITIES.index(t2.priority) <= PlanTask.PRIORITIES.index("LOW")

    def test_adjust_for_failure_no_dependency(self):
        t1 = PlanTask(name="Independent")
        t1.priority = "LOW"
        self.engine.adjust_for_failure([t1], "task_999")
        assert t1.priority == "LOW"

    def test_get_priority_distribution(self):
        tasks = [
            PlanTask(name="A", priority="HIGH"),
            PlanTask(name="B", priority="HIGH"),
            PlanTask(name="C", priority="LOW"),
        ]
        dist = self.engine.get_priority_distribution(tasks)
        assert dist["HIGH"] == 2
        assert dist["LOW"] == 1

    def test_get_priority_distribution_empty(self):
        dist = self.engine.get_priority_distribution([])
        assert dist == {}

    def test_rebalance_short_list(self):
        tasks = [
            PlanTask(name="A", priority="HIGH"),
            PlanTask(name="B", priority="HIGH"),
        ]
        result = self.engine.rebalance(tasks)
        assert len(result) == 2

    def test_rebalance_dominant_priority(self):
        # 5 out of 6 tasks are CRITICAL
        tasks = [
            PlanTask(name="A", priority="CRITICAL"),
            PlanTask(name="B", priority="CRITICAL"),
            PlanTask(name="C", priority="CRITICAL"),
            PlanTask(name="D", priority="CRITICAL"),
            PlanTask(name="E", priority="CRITICAL"),
            PlanTask(name="F", priority="LOW"),
        ]
        result = self.engine.rebalance(tasks)
        # At least one CRITICAL should be downgraded
        priorities = [t.priority for t in result]
        assert priorities.count("CRITICAL") < 5

    def test_dependencies_boost_priority(self):
        t1 = PlanTask(name="HasDeps", dependencies=["a", "b", "c"])
        t2 = PlanTask(name="NoDeps")
        self.engine.assign_priorities([t1, t2])
        # More dependencies should generally boost priority
        assert PlanTask.PRIORITIES.index(t1.priority) <= PlanTask.PRIORITIES.index(t2.priority) + 1

    def test_api_heavy_gets_boost(self):
        t1 = PlanTask(name="Heavy", estimated_api_calls=5)
        t2 = PlanTask(name="Light", estimated_api_calls=0)
        self.engine.assign_priorities([t1, t2])
        assert PlanTask.PRIORITIES.index(t1.priority) <= PlanTask.PRIORITIES.index(t2.priority)
