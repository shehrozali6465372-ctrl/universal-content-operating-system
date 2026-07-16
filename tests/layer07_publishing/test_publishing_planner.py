"""Tests for Layer 7 Module 1 — Publishing Planner."""
import time
from layers.layer07_publishing.modules.publishing_planner.publish_plan import PublishPlan, PlatformTarget
from layers.layer07_publishing.modules.publishing_planner.platform_selector import PlatformSelector
from layers.layer07_publishing.modules.publishing_planner.scheduler import Scheduler
from layers.layer07_publishing.modules.publishing_planner.planner_engine import PlannerEngine


class TestPlatformTarget:
    def test_basic_target(self):
        t = PlatformTarget("facebook", "post")
        assert t.platform == "facebook"
        assert t.status == "pending"

    def test_to_dict(self):
        t = PlatformTarget("instagram", "reel")
        d = t.to_dict()
        assert d["platform"] == "instagram"
        assert d["content_type"] == "reel"


class TestPublishPlan:
    def test_create_plan(self):
        plan = PublishPlan("pp_1", "content_1")
        assert plan.plan_id == "pp_1"

    def test_add_and_get_target(self):
        plan = PublishPlan("pp_1")
        plan.add_target(PlatformTarget("facebook"))
        plan.add_target(PlatformTarget("instagram"))
        assert plan.get_target("facebook") is not None
        assert plan.get_target("twitter") is None

    def test_get_platforms(self):
        plan = PublishPlan("pp_1")
        plan.add_target(PlatformTarget("facebook"))
        plan.add_target(PlatformTarget("linkedin"))
        assert plan.get_platforms() == ["facebook", "linkedin"]

    def test_to_dict(self):
        plan = PublishPlan("pp_1", "c_1")
        d = plan.to_dict()
        assert "plan_id" in d
        assert "targets" in d


class TestPlatformSelector:
    def setup_method(self):
        self.selector = PlatformSelector()

    def test_select_default(self):
        targets = self.selector.select("post")
        assert len(targets) > 0

    def test_select_with_preferred(self):
        targets = self.selector.select("post", preferred_platforms=["facebook", "twitter"])
        assert len(targets) == 2

    def test_select_max_platforms(self):
        targets = self.selector.select("post", max_platforms=3)
        assert len(targets) <= 3

    def test_rank_by_engagement(self):
        ranked = self.selector.rank_by_engagement("post")
        assert len(ranked) > 0

    def test_peak_hours(self):
        hours = self.selector.get_peak_hours("facebook")
        assert len(hours) > 0

    def test_select_count(self):
        self.selector.select("post")
        assert self.selector.select_count == 1


class TestScheduler:
    def setup_method(self):
        self.scheduler = Scheduler()

    def test_schedule_immediate(self):
        plan = PublishPlan("pp_1")
        plan.add_target(PlatformTarget("facebook"))
        self.scheduler.schedule_immediate(plan)
        assert plan.targets[0].scheduled_time is not None

    def test_schedule_optimal(self):
        plan = PublishPlan("pp_1")
        plan.add_target(PlatformTarget("facebook"))
        self.scheduler.schedule_optimal(plan)
        assert plan.targets[0].scheduled_time is not None

    def test_schedule_delayed(self):
        plan = PublishPlan("pp_1")
        plan.add_target(PlatformTarget("twitter"))
        self.scheduler.schedule_delayed(plan, 7200)
        assert plan.targets[0].scheduled_time > time.time()

    def test_stagger(self):
        plan = PublishPlan("pp_1")
        plan.add_target(PlatformTarget("facebook"))
        plan.add_target(PlatformTarget("twitter"))
        plan.add_target(PlatformTarget("linkedin"))
        self.scheduler.stagger(plan, interval_minutes=30)
        times = [t.scheduled_time for t in plan.targets]
        assert times[0] < times[1] < times[2]

    def test_get_scheduled(self):
        plan = PublishPlan("pp_1")
        plan.add_target(PlatformTarget("facebook"))
        self.scheduler.schedule_immediate(plan)
        scheduled = self.scheduler.get_scheduled(plan)
        assert len(scheduled) == 1

    def test_schedule_count(self):
        plan = PublishPlan("pp_1")
        self.scheduler.schedule_immediate(plan)
        assert self.scheduler.schedule_count == 1


class TestPlannerEngine:
    def setup_method(self):
        self.engine = PlannerEngine()

    def test_create_plan(self):
        plan = self.engine.create_plan("content_1", "post")
        assert isinstance(plan, PublishPlan)
        assert len(plan.targets) > 0

    def test_create_plan_with_platforms(self):
        plan = self.engine.create_plan(
            "content_1", "post",
            preferred_platforms=["facebook", "linkedin"],
        )
        assert len(plan.targets) == 2

    def test_create_plan_immediate(self):
        plan = self.engine.create_plan("c_1", "post", schedule_mode="immediate")
        for t in plan.targets:
            assert t.scheduled_time is not None

    def test_create_plan_stagger(self):
        plan = self.engine.create_plan(
            "c_1", "post",
            preferred_platforms=["facebook", "twitter", "linkedin"],
            schedule_mode="stagger",
        )
        times = [t.scheduled_time for t in plan.targets]
        assert times[0] < times[-1]

    def test_create_quick_plan(self):
        plan = self.engine.create_quick_plan("c_1", ["facebook", "twitter"])
        assert len(plan.targets) == 2

    def test_get_plan_summary(self):
        plan = self.engine.create_plan("c_1", "post")
        summary = self.engine.get_plan_summary(plan)
        assert "plan_id" in summary
        assert "platforms" in summary

    def test_metadata_populated(self):
        plan = self.engine.create_plan("c_1", "post")
        assert "content_type" in plan.metadata

    def test_plan_count(self):
        self.engine.create_plan("c_1", "post")
        assert self.engine.plan_count == 1

    def test_video_content(self):
        plan = self.engine.create_plan("c_1", "video")
        platforms = plan.get_platforms()
        assert "youtube" in platforms
