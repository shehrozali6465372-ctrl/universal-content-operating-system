"""Tests for Layer 10 Module 5 — Autonomous Decision & Planning Engine."""
from layers.layer10_monetization.modules.autonomous_planner.autonomous_planner import AutonomousPlanner
from layers.layer10_monetization.modules.autonomous_planner.goal_decomposer import GoalDecomposer
from layers.layer10_monetization.modules.autonomous_planner.decision_matrix import DecisionMatrix
from layers.layer10_monetization.modules.autonomous_planner.scenario_simulator import ScenarioSimulator
from layers.layer10_monetization.modules.autonomous_planner.resource_planner import ResourcePlanner
from layers.layer10_monetization.modules.autonomous_planner.risk_manager import RiskManager, Risk
from layers.layer10_monetization.modules.autonomous_planner.adaptive_planner import AdaptivePlanner
from layers.layer10_monetization.modules.autonomous_planner.opportunity_detector import OpportunityDetector
from layers.layer10_monetization.modules.autonomous_planner.plan_memory import PlanMemory
from layers.layer10_monetization.modules.autonomous_planner.planning_metrics import PlanningMetrics
from layers.layer10_monetization.modules.autonomous_planner.planning_report_generator import PlanningReportGenerator
from layers.layer10_monetization.modules.autonomous_planner.autonomous_planning_manager import AutonomousPlanningManager


# ─── AutonomousPlanner Tests ─────────────────────────────────────
class TestAutonomousPlanner:
    def setup_method(self):
        self.ap = AutonomousPlanner()

    def test_create_plan(self):
        plan = self.ap.create_plan("Grow audience", steps=[
            {"layer": "layer04", "action": "draft"},
            {"layer": "layer07", "action": "publish"},
        ])
        assert plan.plan_id.startswith("aplan_")
        assert plan.goal == "Grow audience"
        assert len(plan.steps) == 2

    def test_plan_progress(self):
        plan = self.ap.create_plan("Test", steps=[
            {"layer": "l1", "action": "a"}, {"layer": "l2", "action": "b"},
        ])
        plan.steps[0].status = "completed"
        assert plan.progress == 0.5

    def test_plan_is_complete(self):
        plan = self.ap.create_plan("Test", steps=[{"layer": "l1", "action": "a"}])
        plan.steps[0].status = "completed"
        assert plan.is_complete is True

    def test_replan(self):
        plan = self.ap.create_plan("Test", steps=[{"layer": "l1", "action": "a"}])
        result = self.ap.replan(plan.plan_id, [{"layer": "l2", "action": "b"}])
        assert result is not None
        assert len(result.steps) == 1
        assert result.replan_count == 1

    def test_get_active_plans(self):
        self.ap.create_plan("P1")
        self.ap.create_plan("P2")
        active = self.ap.get_active_plans()
        assert len(active) == 2

    def test_stats(self):
        self.ap.create_plan("P1")
        stats = self.ap.get_stats()
        assert stats["total_plans"] == 1


# ─── GoalDecomposer Tests ────────────────────────────────────────
class TestGoalDecomposer:
    def setup_method(self):
        self.gd = GoalDecomposer()

    def test_decompose(self):
        result = self.gd.decompose("Grow audience", "grow_audience")
        assert result.goal == "Grow audience"
        assert len(result.milestones) > 0

    def test_custom_decomposition(self):
        custom = [("Phase 1", [("layer01", "action1", "desc1")])]
        result = self.gd.decompose("Test", custom_milestones=custom)
        assert len(result.milestones) == 1

    def test_add_milestone(self):
        result = self.gd.decompose("Test")
        ms = self.gd.add_milestone(result.decomposition_id, "Extra Phase")
        assert ms is not None

    def test_get_stats(self):
        self.gd.decompose("Test", "grow_audience")
        stats = self.gd.get_stats()
        assert stats["total_decompositions"] == 1
        assert stats["total_milestones"] > 0


# ─── DecisionMatrix Tests ────────────────────────────────────────
class TestDecisionMatrix:
    def setup_method(self):
        self.dm = DecisionMatrix()

    def test_add_option(self):
        opt = self.dm.add_option("option_a")
        assert opt.option_id.startswith("opt_")
        assert opt.name == "option_a"

    def test_set_score(self):
        opt = self.dm.add_option("a")
        opt.set_score("impact", 0.8)
        assert opt.scores["impact"] == 0.8

    def test_evaluate(self):
        a = self.dm.add_option("a")
        a.set_score("impact", 0.9); a.set_score("risk", 0.2)
        b = self.dm.add_option("b")
        b.set_score("impact", 0.5); b.set_score("risk", 0.5)
        best = self.dm.evaluate()
        assert best.name == "a"

    def test_risk_reward(self):
        opt = self.dm.add_option("a")
        opt.set_score("impact", 0.8); opt.set_score("risk", 0.3)
        rr = self.dm.risk_reward_analysis(opt)
        assert "risk" in rr and "reward" in rr

    def test_cost_benefit(self):
        opt = self.dm.add_option("a")
        opt.set_score("impact", 0.8); opt.set_score("cost", 0.3)
        cb = self.dm.cost_benefit(opt)
        assert cb["net"] == 0.5

    def test_set_factor_weight(self):
        self.dm.set_factor_weight("impact", 2.0)
        assert self.dm._factor_weights["impact"] == 2.0

    def test_stats(self):
        self.dm.add_option("a")
        stats = self.dm.get_stats()
        assert stats["options"] == 1


# ─── ScenarioSimulator Tests ─────────────────────────────────────
class TestScenarioSimulator:
    def setup_method(self):
        self.ss = ScenarioSimulator()

    def test_create_scenario(self):
        scenario = self.ss.create_scenario("primary", [
            {"layer": "l1", "action": "a"},
        ])
        assert scenario.scenario_id.startswith("scen_")
        assert len(scenario.steps) == 1

    def test_simulate(self):
        scenario = self.ss.create_scenario("test")
        result = self.ss.simulate(scenario.scenario_id)
        assert result is not None
        assert result.confidence > 0
        assert result.simulated_at > 0

    def test_compare_scenarios(self):
        self.ss.create_scenario("s1", [{"layer": "l1", "action": "a"}])
        self.ss.create_scenario("s2", [{"layer": "l1", "action": "a"}, {"layer": "l2", "action": "b"}])
        for s in self.ss._scenarios:
            self.ss.simulate(s.scenario_id)
        ranked = self.ss.compare_scenarios()
        assert len(ranked) == 2

    def test_choose_best(self):
        self.ss.create_scenario("s1")
        self.ss.create_scenario("s2")
        for s in self.ss._scenarios:
            self.ss.simulate(s.scenario_id)
        best = self.ss.choose_best()
        assert best is not None

    def test_stats(self):
        self.ss.create_scenario("s1")
        stats = self.ss.get_stats()
        assert stats["total_scenarios"] == 1


# ─── ResourcePlanner Tests ───────────────────────────────────────
class TestResourcePlanner:
    def setup_method(self):
        self.rp = ResourcePlanner()

    def test_plan_for_layers(self):
        plan = self.rp.plan_for_layers(["layer01_core", "layer04_writing"])
        assert plan.cpu_cores > 0
        assert plan.api_calls > 0

    def test_estimate_cost(self):
        cost = self.rp.estimate_cost(["layer04_writing", "layer07_publishing"])
        assert cost > 0

    def test_check_budget(self):
        plan = self.rp.plan_for_layers(["layer01_core"])
        assert self.rp.check_budget(plan) is True

    def test_budget_limit(self):
        rp = ResourcePlanner(budget_limit=0.001)
        cost = rp.estimate_cost(["layer04_writing", "layer05_image", "layer09_learning"])
        assert cost > 0.001, f"Cost {cost} should exceed budget limit 0.001"

    def test_stats(self):
        self.rp.plan_for_layers(["layer01_core"])
        stats = self.rp.get_stats()
        assert stats["total_plans"] == 1


# ─── RiskManager Tests ───────────────────────────────────────────
class TestRiskManager:
    def setup_method(self):
        self.rm = RiskManager()

    def test_detect_risks(self):
        risks = self.rm.detect_risks(["layer07_publishing", "layer05_image"])
        assert len(risks) > 0

    def test_assess_risk(self):
        risks = self.rm.detect_risks(["layer07_publishing"])
        if risks:
            assessment = self.rm.assess_risk(risks[0])
            assert "risk_id" in assessment

    def test_suggest_rollback(self):
        risk = Risk("platform", "Test")
        risk.level = "critical"
        risk.probability = 0.9
        risk.impact = 0.9
        assert self.rm.suggest_rollback([risk]) is True

    def test_get_high_risks(self):
        self.rm.detect_risks(["layer07_publishing"])
        high = self.rm.get_high_risks()
        assert isinstance(high, list)

    def test_stats(self):
        self.rm.detect_risks(["layer07_publishing"])
        stats = self.rm.get_stats()
        assert stats["total_risks"] > 0


# ─── AdaptivePlanner Tests ───────────────────────────────────────
class TestAdaptivePlanner:
    def setup_method(self):
        self.ap = AdaptivePlanner()

    def test_adapt_on_failure(self):
        event = self.ap.adapt_on_failure("p1", "layer04", "timeout")
        assert event.trigger == "failure"
        assert len(event.changes) > 0

    def test_adapt_on_analytics_low(self):
        event = self.ap.adapt_on_analytics("p1", "engagement", 0.2)
        assert event.trigger == "analytics"
        assert any(c["action"] == "adjust_strategy" for c in event.changes)

    def test_adapt_on_analytics_high(self):
        event = self.ap.adapt_on_analytics("p1", "engagement", 0.9)
        assert any(c["action"] == "scale_up" for c in event.changes)

    def test_adapt_on_timeout(self):
        event = self.ap.adapt_on_timeout("p1", "layer04")
        assert event.trigger == "timeout"

    def test_stats(self):
        self.ap.adapt_on_failure("p1", "l1", "err")
        self.ap.adapt_on_timeout("p1", "l1")
        stats = self.ap.get_stats()
        assert stats["total_adaptations"] == 2


# ─── OpportunityDetector Tests ───────────────────────────────────
class TestOpportunityDetector:
    def setup_method(self):
        self.od = OpportunityDetector()

    def test_scan(self):
        opps = self.od.scan({"platform": "tiktok"})
        assert len(opps) > 0

    def test_scan_universal(self):
        opps = self.od.scan({})
        assert len(opps) >= 2

    def test_get_top_opportunities(self):
        self.od.scan({})
        top = self.od.get_top_opportunities(2)
        assert len(top) <= 2

    def test_stats(self):
        self.od.scan({})
        stats = self.od.get_stats()
        assert stats["total"] > 0


# ─── PlanMemory Tests ────────────────────────────────────────────
class TestPlanMemory:
    def setup_method(self):
        self.pm = PlanMemory()

    def test_store(self):
        entry = self.pm.store("grow_audience", "Test", steps_count=5, success=True)
        assert entry.entry_id.startswith("pmem_")
        assert entry.success is True

    def test_search(self):
        self.pm.store("grow", "G1", success=True)
        self.pm.store("engage", "E1", success=False)
        results = self.pm.search(plan_type="grow")
        assert len(results) == 1

    def test_get_successful_plans(self):
        self.pm.store("a", "G1", success=True)
        self.pm.store("b", "G2", success=False)
        successful = self.pm.get_successful_plans()
        assert len(successful) == 1

    def test_get_templates(self):
        self.pm.store("grow", "G1", success=True)
        self.pm.store("grow", "G2", success=True)
        templates = self.pm.get_templates()
        assert templates["grow"] == 2

    def test_stats(self):
        self.pm.store("a", "G1", success=True)
        stats = self.pm.get_stats()
        assert stats["total"] == 1
        assert stats["successful"] == 1


# ─── PlanningMetrics Tests ───────────────────────────────────────
class TestPlanningMetrics:
    def setup_method(self):
        self.pm = PlanningMetrics()

    def test_record_plan(self):
        self.pm.record_plan(success=True, execution_time_ms=100, decision_score=0.8)
        assert self.pm._total_plans == 1

    def test_success_rate(self):
        self.pm.record_plan(success=True)
        self.pm.record_plan(success=True)
        self.pm.record_plan(success=False)
        rate = self.pm.get_success_rate()
        assert abs(rate - 0.667) < 0.01

    def test_avg_execution_time(self):
        self.pm.record_plan(execution_time_ms=100)
        self.pm.record_plan(execution_time_ms=200)
        assert self.pm.get_avg_execution_time() == 150.0

    def test_summary(self):
        self.pm.record_plan(success=True)
        summary = self.pm.get_summary()
        assert "total_plans" in summary
        assert "success_rate" in summary


# ─── PlanningReportGenerator Tests ───────────────────────────────
class TestPlanningReportGenerator:
    def setup_method(self):
        self.prg = PlanningReportGenerator()

    def test_generate(self):
        report = self.prg.generate("planning", {"goal": "test"})
        assert report.report_id.startswith("prep_")

    def test_add_recommendation(self):
        report = self.prg.generate("risk")
        report.add_recommendation("Reduce risk")
        assert len(report.recommendations) == 1

    def test_export_dict(self):
        report = self.prg.generate("resource", {"cpu": 4})
        d = report.export_dict()
        assert "planning" in d
        assert "recommendations" in d

    def test_stats(self):
        self.prg.generate("planning")
        stats = self.prg.get_stats()
        assert stats["total_reports"] == 1


# ─── AutonomousPlanningManager Tests ─────────────────────────────
class TestAutonomousPlanningManager:
    def setup_method(self):
        self.mgr = AutonomousPlanningManager()

    def test_plan(self):
        result = self.mgr.plan("Grow audience", "grow_audience")
        assert result["ready_for_execution"] is True
        assert "plan_id" in result
        assert "report_id" in result
        assert result["duration_ms"] > 0

    def test_plan_stages(self):
        result = self.mgr.plan("Test", "grow_audience")
        stages = result["stages"]
        assert "decompose" in stages
        assert "decision" in stages
        assert "simulation" in stages
        assert "resources" in stages
        assert "risks" in stages
        assert "plan" in stages

    def test_adapt_plan_failure(self):
        result = self.mgr.plan("Test")
        adapt = self.mgr.adapt_plan(result["plan_id"], "failure",
                                     {"layer": "layer04", "error": "timeout"})
        assert "event_id" in adapt

    def test_adapt_plan_analytics(self):
        result = self.mgr.plan("Test")
        adapt = self.mgr.adapt_plan(result["plan_id"], "analytics",
                                     {"metric": "engagement", "value": 0.2})
        assert "event_id" in adapt

    def test_health(self):
        self.mgr.plan("Test")
        health = self.mgr.get_health()
        assert "total_plans" in health
        assert "metrics" in health

    def test_multiple_plans(self):
        for i in range(3):
            self.mgr.plan(f"Goal {i}", "grow_audience")
        assert self.mgr.get_health()["total_plans"] == 3


# ─── Integration Tests ───────────────────────────────────────────
class TestAutonomousPlanningIntegration:
    def setup_method(self):
        self.mgr = AutonomousPlanningManager()

    def test_full_pipeline(self):
        result = self.mgr.plan(
            "Grow audience on LinkedIn with AI content",
            "grow_audience",
            context={"platform": "linkedin", "topic": "AI"},
        )
        assert result["ready_for_execution"] is True
        assert len(result["stages"]) >= 6

    def test_cross_platform_pipeline(self):
        platforms = ["facebook", "instagram", "linkedin", "x"]
        results = []
        for platform in platforms:
            r = self.mgr.plan(f"Content for {platform}", "grow_audience",
                               context={"platform": platform})
            results.append(r)
        assert len(results) == 4
        assert all(r["ready_for_execution"] for r in results)

    def test_plan_with_adaptation(self):
        result = self.mgr.plan("Test goal")
        plan_id = result["plan_id"]
        self.mgr.adapt_plan(plan_id, "failure", {"layer": "layer04", "error": "API error"})
        self.mgr.adapt_plan(plan_id, "analytics", {"metric": "engagement", "value": 0.1})
        health = self.mgr.get_health()
        assert health["total_adaptations"] == 2

    def test_resource_planning_integration(self):
        result = self.mgr.plan("Complex goal", "grow_audience")
        resources = result["stages"]["resources"]
        assert resources["cpu_cores"] > 0
        assert resources["time_estimate_seconds"] > 0

    def test_risk_and_opportunity_integration(self):
        result = self.mgr.plan("Test", "grow_audience", context={"platform": "tiktok"})
        assert result["stages"]["risks"]["count"] >= 0
        assert result["stages"]["opportunities"]["count"] > 0

    def test_memory_and_metrics(self):
        self.mgr.plan("Goal 1")
        self.mgr.plan("Goal 2")
        health = self.mgr.get_health()
        assert health["memory"]["total"] == 2
        assert health["metrics"]["total_plans"] == 2
