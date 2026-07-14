"""Tests for ResearchPlan and PlanTask."""

from layers.layer02_research.modules.research_planner.research_plan import PlanTask, ResearchPlan


class TestPlanTask:
    def test_create_task(self):
        task = PlanTask(name="Discover trends", module="trend_discovery")
        assert task.name == "Discover trends"
        assert task.module == "trend_discovery"
        assert task.status == "pending"
        assert task.priority == "MEDIUM"

    def test_task_id_unique(self):
        t1 = PlanTask(name="Task A")
        t2 = PlanTask(name="Task B")
        assert t1.task_id != t2.task_id

    def test_start_task(self):
        task = PlanTask(name="Test")
        task.start()
        assert task.status == "running"
        assert task.started_at != ""

    def test_complete_task(self):
        task = PlanTask(name="Test")
        task.start()
        task.complete(result={"score": 90}, confidence=0.92)
        assert task.status == "completed"
        assert task.confidence == 0.92
        assert task.completed_at != ""

    def test_fail_task(self):
        task = PlanTask(name="Test")
        task.start()
        task.fail()
        assert task.status == "failed"

    def test_skip_task(self):
        task = PlanTask(name="Test")
        task.skip()
        assert task.status == "skipped"

    def test_to_dict(self):
        task = PlanTask(name="Test", module="trend_discovery", priority="HIGH")
        d = task.to_dict()
        assert d["name"] == "Test"
        assert d["module"] == "trend_discovery"
        assert d["priority"] == "HIGH"
        assert "task_id" in d

    def test_dependencies(self):
        task = PlanTask(name="Verify", dependencies=["task_123", "task_456"])
        assert len(task.dependencies) == 2

    def test_invalid_priority_fallback(self):
        task = PlanTask(name="Test", priority="INVALID")
        assert task.priority == "MEDIUM"

    def test_negative_estimates_clamped(self):
        task = PlanTask(name="Test", estimated_time_min=-5, estimated_api_calls=-3)
        assert task.estimated_time_min == 0.0
        assert task.estimated_api_calls == 0


class TestResearchPlan:
    def test_create_plan(self):
        plan = ResearchPlan(topic="AI Jobs")
        assert plan.topic == "AI Jobs"
        assert plan.status == "draft"
        assert plan.tasks == []

    def test_add_task(self):
        plan = ResearchPlan(topic="AI Jobs")
        task = PlanTask(name="Discover trends")
        plan.add_task(task)
        assert len(plan.tasks) == 1

    def test_remove_task(self):
        plan = ResearchPlan(topic="AI Jobs")
        task = PlanTask(name="Discover trends")
        plan.add_task(task)
        removed = plan.remove_task(task.task_id)
        assert removed is True
        assert len(plan.tasks) == 0

    def test_remove_nonexistent_task(self):
        plan = ResearchPlan(topic="AI Jobs")
        removed = plan.remove_task("nonexistent_id")
        assert removed is False

    def test_get_task(self):
        plan = ResearchPlan(topic="AI Jobs")
        task = PlanTask(name="Discover trends")
        plan.add_task(task)
        found = plan.get_task(task.task_id)
        assert found is not None
        assert found.name == "Discover trends"

    def test_get_ready_tasks(self):
        plan = ResearchPlan(topic="AI Jobs")
        t1 = PlanTask(name="Step 1")
        t2 = PlanTask(name="Step 2", dependencies=[t1.task_id])
        plan.add_task(t1)
        plan.add_task(t2)
        ready = plan.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == t1.task_id

    def test_get_ready_tasks_after_completion(self):
        plan = ResearchPlan(topic="AI Jobs")
        t1 = PlanTask(name="Step 1")
        t2 = PlanTask(name="Step 2", dependencies=[t1.task_id])
        plan.add_task(t1)
        plan.add_task(t2)
        t1.complete()
        ready = plan.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == t2.task_id

    def test_get_progress_empty(self):
        plan = ResearchPlan(topic="AI Jobs")
        assert plan.get_progress() == 0.0

    def test_get_progress(self):
        plan = ResearchPlan(topic="AI Jobs")
        t1 = PlanTask(name="A")
        t2 = PlanTask(name="B")
        plan.add_task(t1)
        plan.add_task(t2)
        t1.complete()
        assert plan.get_progress() == 0.5

    def test_recalculate_totals(self):
        plan = ResearchPlan(topic="AI Jobs")
        t1 = PlanTask(name="A", estimated_time_min=5.0, estimated_api_calls=2)
        t2 = PlanTask(name="B", estimated_time_min=3.0, estimated_api_calls=1)
        plan.add_task(t1)
        plan.add_task(t2)
        assert plan.total_estimated_time_min == 8.0
        assert plan.total_estimated_api_calls == 3

    def test_to_dict(self):
        plan = ResearchPlan(topic="AI Jobs", niche="technology")
        d = plan.to_dict()
        assert d["topic"] == "AI Jobs"
        assert d["niche"] == "technology"
        assert "tasks" in d

    def test_from_dict_roundtrip(self):
        plan = ResearchPlan(topic="AI Jobs")
        plan.add_task(PlanTask(name="Step 1", module="trend_discovery"))
        plan.add_task(PlanTask(name="Step 2", module="fact_verification"))
        d = plan.to_dict()
        restored = ResearchPlan.from_dict(d)
        assert restored.topic == "AI Jobs"
        assert len(restored.tasks) == 2
        assert restored.total_estimated_api_calls == plan.total_estimated_api_calls

    def test_critical_path(self):
        plan = ResearchPlan(topic="AI Jobs")
        t1 = PlanTask(name="A")
        t2 = PlanTask(name="B", dependencies=[t1.task_id])
        t3 = PlanTask(name="C", dependencies=[t2.task_id])
        plan.add_task(t1)
        plan.add_task(t2)
        plan.add_task(t3)
        cp = plan.get_critical_path()
        assert len(cp) == 3
