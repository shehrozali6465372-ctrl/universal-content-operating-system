"""Tests for Layer 10 Module 4 — AI Meta Controller."""
from layers.layer10_monetization.modules.ai_meta_controller.meta_controller import MetaController
from layers.layer10_monetization.modules.ai_meta_controller.goal_manager import GoalManager
from layers.layer10_monetization.modules.ai_meta_controller.strategy_selector import StrategySelector
from layers.layer10_monetization.modules.ai_meta_controller.decision_engine import DecisionEngine
from layers.layer10_monetization.modules.ai_meta_controller.context_manager import ContextManager
from layers.layer10_monetization.modules.ai_meta_controller.objective_planner import ObjectivePlanner
from layers.layer10_monetization.modules.ai_meta_controller.ai_coordinator import AICoordinator
from layers.layer10_monetization.modules.ai_meta_controller.conflict_resolver import ConflictResolver
from layers.layer10_monetization.modules.ai_meta_controller.policy_arbiter import PolicyArbiter
from layers.layer10_monetization.modules.ai_meta_controller.performance_optimizer import PerformanceOptimizer
from layers.layer10_monetization.modules.ai_meta_controller.meta_memory import MetaMemory
from layers.layer10_monetization.modules.ai_meta_controller.meta_metrics import MetaMetrics
from layers.layer10_monetization.modules.ai_meta_controller.meta_report_generator import MetaReportGenerator
from layers.layer10_monetization.modules.ai_meta_controller.self_reflection_engine import SelfReflectionEngine
from layers.layer10_monetization.modules.ai_meta_controller.global_orchestrator_api import GlobalOrchestratorAPI


# ─── MetaController Tests ────────────────────────────────────────
class TestMetaController:
    def setup_method(self):
        self.mc = MetaController()

    def test_start(self):
        cid = self.mc.start()
        assert cid.startswith("mc_")
        assert self.mc.status == "running"

    def test_stop(self):
        self.mc.start()
        assert self.mc.stop() is True
        assert self.mc.status == "stopped"

    def test_stop_when_idle(self):
        assert self.mc.stop() is False

    def test_pause_resume(self):
        self.mc.start()
        assert self.mc.pause() is True
        assert self.mc.status == "paused"
        assert self.mc.resume() is True
        assert self.mc.status == "running"

    def test_register_layer(self):
        self.mc.register_layer("layer04", lambda ctx: "ok")
        assert "layer04" in self.mc._layer_handlers

    def test_coordinate_layers(self):
        self.mc.register_layer("layer04", lambda ctx: {"draft": "text"})
        self.mc.register_layer("layer06", lambda ctx: {"score": 95})
        results = self.mc.coordinate_layers(["layer04", "layer06"])
        assert results["layer04"]["draft"] == "text"
        assert results["layer06"]["score"] == 95

    def test_evaluate_system(self):
        self.mc.start()
        eval_result = self.mc.evaluate_system()
        assert "status" in eval_result
        assert eval_result["status"] == "running"

    def test_self_improve(self):
        result = self.mc.self_improve()
        assert "improvements_identified" in result

    def test_get_state(self):
        state = self.mc.get_state()
        assert "controller_id" in state
        assert "status" in state


# ─── GoalManager Tests ───────────────────────────────────────────
class TestGoalManager:
    def setup_method(self):
        self.gm = GoalManager()

    def test_create_goal(self):
        goal = self.gm.create_goal("Increase followers", priority="high")
        assert goal.goal_id.startswith("goal_")
        assert goal.name == "Increase followers"
        assert goal.status == "active"

    def test_update_goal(self):
        goal = self.gm.create_goal("Test")
        updated = self.gm.update_goal(goal.goal_id, priority="critical")
        assert updated.priority == "critical"

    def test_complete_goal(self):
        goal = self.gm.create_goal("Test")
        completed = self.gm.complete_goal(goal.goal_id)
        assert completed.status == "completed"

    def test_cancel_goal(self):
        goal = self.gm.create_goal("Test")
        cancelled = self.gm.cancel_goal(goal.goal_id)
        assert cancelled.status == "cancelled"

    def test_get_active_goals(self):
        self.gm.create_goal("G1")
        self.gm.create_goal("G2")
        active = self.gm.get_active_goals()
        assert len(active) == 2

    def test_prioritize_goals(self):
        self.gm.create_goal("Low", priority="low")
        self.gm.create_goal("Critical", priority="critical")
        prioritized = self.gm.prioritize_goals()
        assert prioritized[0].priority == "critical"

    def test_progress(self):
        goal = self.gm.create_goal("Test", target_metric="followers", target_value=1000)
        goal.current_value = 500
        assert goal.progress == 0.5

    def test_get_stats(self):
        self.gm.create_goal("G1")
        stats = self.gm.get_stats()
        assert stats["total"] == 1
        assert stats["active"] == 1


# ─── StrategySelector Tests ──────────────────────────────────────
class TestStrategySelector:
    def setup_method(self):
        self.ss = StrategySelector()

    def test_select_default(self):
        strategy = self.ss.select({})
        assert strategy.name in ("educational", "news", "entertainment", "marketing", "branding", "sales", "awareness", "community", "viral", "seasonal")

    def test_select_by_platform(self):
        strategy = self.ss.select({"platform": "linkedin"})
        assert strategy.name in self.ss.get_all_strategies()

    def test_set_platform_strategy(self):
        result = self.ss.set_platform_strategy("tiktok", "entertainment")
        assert result is True

    def test_get_strategy(self):
        strategy = self.ss.get_strategy("educational")
        assert strategy is not None
        assert strategy.name == "educational"

    def test_get_all_strategies(self):
        strategies = self.ss.get_all_strategies()
        assert len(strategies) == 10
        assert "educational" in strategies

    def test_history(self):
        self.ss.select({"platform": "facebook"})
        history = self.ss.get_history()
        assert len(history) == 1


# ─── DecisionEngine Tests ────────────────────────────────────────
class TestDecisionEngine:
    def setup_method(self):
        self.de = DecisionEngine()

    def test_decide_high_quality(self):
        decision = self.de.decide({"quality_score": 0.9, "risk_level": "low"})
        assert decision.action == "publish_now"
        assert decision.confidence > 0.5

    def test_decide_low_quality(self):
        decision = self.de.decide({"quality_score": 0.3})
        assert decision.action == "rewrite"

    def test_decide_conflicts(self):
        decision = self.de.decide({"quality_score": 0.7, "has_conflicts": True})
        assert decision.action == "human_review"

    def test_decide_high_risk(self):
        decision = self.de.decide({"quality_score": 0.7, "risk_level": "high"})
        assert decision.action == "wait"

    def test_get_recent(self):
        for _ in range(3):
            self.de.decide({"quality_score": 0.7})
        recent = self.de.get_recent(2)
        assert len(recent) == 2

    def test_decision_to_dict(self):
        decision = self.de.decide({"quality_score": 0.9})
        d = decision.to_dict()
        assert "decision_id" in d
        assert "action" in d
        assert "confidence" in d


# ─── ContextManager Tests ────────────────────────────────────────
class TestContextManager:
    def setup_method(self):
        self.cm = ContextManager()

    def test_set_get(self):
        self.cm.set("platform", "linkedin")
        assert self.cm.get("platform") == "linkedin"

    def test_get_default(self):
        assert self.cm.get("nonexistent", "default") == "default"

    def test_update(self):
        self.cm.update({"platform": "x", "topic": "AI"})
        assert self.cm.get("platform") == "x"
        assert self.cm.get("topic") == "AI"

    def test_snapshot(self):
        self.cm.set("platform", "facebook")
        snap = self.cm.snapshot()
        assert snap["platform"] == "facebook"

    def test_restore(self):
        self.cm.set("platform", "facebook")
        self.cm.snapshot()
        self.cm.set("platform", "x")
        self.cm.restore()
        assert self.cm.get("platform") == "facebook"

    def test_clear(self):
        self.cm.set("platform", "facebook")
        self.cm.clear()
        assert self.cm.get("platform") == ""

    def test_get_all(self):
        self.cm.set("platform", "x")
        all_ctx = self.cm.get_all()
        assert "platform" in all_ctx


# ─── ObjectivePlanner Tests ──────────────────────────────────────
class TestObjectivePlanner:
    def setup_method(self):
        self.op = ObjectivePlanner()

    def test_create_plan(self):
        plan = self.op.create_plan("goal_1", "grow_followers")
        assert plan.plan_id.startswith("plan_")
        assert len(plan.steps) == 8

    def test_create_custom_plan(self):
        steps = [{"layer": "l1", "action": "do"}, {"layer": "l2", "action": "do2"}]
        plan = self.op.create_plan("goal_1", custom_steps=steps)
        assert len(plan.steps) == 2

    def test_get_plan(self):
        plan = self.op.create_plan("goal_1")
        found = self.op.get_plan(plan.plan_id)
        assert found is not None

    def test_is_complete(self):
        plan = self.op.create_plan("goal_1", "increase_engagement")
        assert plan.is_complete is False

    def test_add_step(self):
        plan = self.op.create_plan("goal_1")
        step = plan.add_step("layer01", "test", "Test step")
        assert step["layer"] == "layer01"

    def test_get_stats(self):
        self.op.create_plan("goal_1")
        stats = self.op.get_stats()
        assert stats["total_plans"] == 1


# ─── AICoordinator Tests ────────────────────────────────────────
class TestAICoordinator:
    def setup_method(self):
        self.ac = AICoordinator()

    def test_activate_engine(self):
        assert self.ac.activate_engine("writing_ai") is True
        assert self.ac.get_engine_state("writing_ai") == "active"

    def test_deactivate_engine(self):
        self.ac.activate_engine("writing_ai")
        assert self.ac.deactivate_engine("writing_ai") is True
        assert self.ac.get_engine_state("writing_ai") == "idle"

    def test_activate_nonexistent(self):
        assert self.ac.activate_engine("nonexistent") is False

    def test_get_active_engines(self):
        self.ac.activate_engine("writing_ai")
        self.ac.activate_engine("quality_ai")
        active = self.ac.get_active_engines()
        assert len(active) == 2

    def test_coordinate_batch(self):
        results = self.ac.coordinate_batch(["writing_ai", "quality_ai"])
        assert results["writing_ai"] == "activated"

    def test_diagnostics(self):
        self.ac.activate_engine("writing_ai")
        diag = self.ac.get_diagnostics()
        assert diag["active"] == 1
        assert diag["total_engines"] == 8


# ─── ConflictResolver Tests ──────────────────────────────────────
class TestConflictResolver:
    def setup_method(self):
        self.cr = ConflictResolver()

    def test_detect_conflict(self):
        suggestions = {"writing_ai": "publish", "quality_ai": "revise"}
        conflict = self.cr.detect_conflict(suggestions)
        assert conflict is not None
        assert conflict.resolved is False

    def test_no_conflict(self):
        suggestions = {"writing_ai": "publish", "quality_ai": "publish"}
        conflict = self.cr.detect_conflict(suggestions)
        assert conflict is None

    def test_resolve(self):
        suggestions = {"writing_ai": "publish", "quality_ai": "revise"}
        conflict = self.cr.detect_conflict(suggestions)
        resolved = self.cr.resolve(conflict.conflict_id, strategy="priority")
        assert resolved.resolved is True
        assert resolved.resolution == "writing_ai"

    def test_resolve_nonexistent(self):
        result = self.cr.resolve("nonexistent")
        assert result is None

    def test_get_unresolved(self):
        suggestions = {"a": "publish", "b": "revise"}
        self.cr.detect_conflict(suggestions)
        unresolved = self.cr.get_unresolved()
        assert len(unresolved) == 1

    def test_stats(self):
        suggestions = {"a": "publish", "b": "revise"}
        self.cr.detect_conflict(suggestions)
        stats = self.cr.get_stats()
        assert stats["total"] == 1
        assert stats["unresolved"] == 1


# ─── PolicyArbiter Tests ─────────────────────────────────────────
class TestPolicyArbiter:
    def setup_method(self):
        self.pa = PolicyArbiter()

    def test_check_safe(self):
        result = self.pa.check("Great post about technology!", {})
        assert result["passed"] is True

    def test_check_unsafe(self):
        result = self.pa.check("This contains hate speech and violence", {})
        assert result["passed"] is False
        assert len(result["violations"]) > 0

    def test_add_rule(self):
        rule = self.pa.add_rule("custom", "my_rule", "My custom rule")
        assert rule.rule_id.startswith("rule_")

    def test_get_rules(self):
        rules = self.pa.get_rules("safety")
        assert len(rules) > 0

    def test_get_violations(self):
        self.pa.check("hate and violence", {})
        violations = self.pa.get_violations()
        assert len(violations) > 0

    def test_stats(self):
        stats = self.pa.get_stats()
        assert stats["total_rules"] > 0


# ─── PerformanceOptimizer Tests ──────────────────────────────────
class TestPerformanceOptimizer:
    def setup_method(self):
        self.po = PerformanceOptimizer()

    def test_record_metric(self):
        self.po.record_metric("latency_ms", 100)
        self.po.record_metric("latency_ms", 200)
        assert self.po.get_average("latency_ms") == 150.0

    def test_analyze(self):
        self.po.record_metric("cpu_usage", 0.5)
        self.po.record_metric("cpu_usage", 0.7)
        analysis = self.po.analyze()
        assert "cpu_usage" in analysis
        assert analysis["cpu_usage"]["avg"] == 0.6

    def test_suggest_optimizations_high_latency(self):
        for _ in range(5):
            self.po.record_metric("latency_ms", 2000)
        suggestions = self.po.suggest_optimizations()
        assert any(s["type"] == "latency" for s in suggestions)

    def test_suggest_optimizations_high_cpu(self):
        for _ in range(5):
            self.po.record_metric("cpu_usage", 0.9)
        suggestions = self.po.suggest_optimizations()
        assert any(s["type"] == "cpu" for s in suggestions)

    def test_stats(self):
        self.po.record_metric("latency_ms", 100)
        stats = self.po.get_stats()
        assert "analysis" in stats


# ─── MetaMemory Tests ────────────────────────────────────────────
class TestMetaMemory:
    def setup_method(self):
        self.mm = MetaMemory()

    def test_store(self):
        entry = self.mm.store("lesson", "Engagement improved with hooks", importance=0.8)
        assert entry.entry_id.startswith("mem_")
        assert entry.category == "lesson"

    def test_search(self):
        self.mm.store("lesson", "Lesson 1")
        self.mm.store("failure", "Failed attempt")
        results = self.mm.search(category="lesson")
        assert len(results) == 1

    def test_search_by_tag(self):
        self.mm.store("lesson", "L1", tags=["facebook"])
        self.mm.store("lesson", "L2", tags=["linkedin"])
        results = self.mm.search(tag="facebook")
        assert len(results) == 1

    def test_get_recent(self):
        for _ in range(5):
            self.mm.store("lesson", "L")
        recent = self.mm.get_recent(3)
        assert len(recent) == 3

    def test_stats(self):
        self.mm.store("lesson", "L1")
        self.mm.store("failure", "F1")
        stats = self.mm.get_stats()
        assert stats["total"] == 2
        assert stats["by_category"]["lesson"] == 1


# ─── MetaMetrics Tests ───────────────────────────────────────────
class TestMetaMetrics:
    def setup_method(self):
        self.mm = MetaMetrics()

    def test_record_decision(self):
        self.mm.record_decision(correct=True)
        self.mm.record_decision(correct=True)
        self.mm.record_decision(correct=False)
        assert abs(self.mm.get_metric("decision_accuracy") - 0.667) < 0.01

    def test_record_goal(self):
        self.mm.record_goal(completed=True)
        assert self.mm.get_metric("goal_completion_rate") == 1.0

    def test_record_recovery(self):
        self.mm.record_recovery(successful=True)
        self.mm.record_recovery(successful=False)
        assert self.mm.get_metric("recovery_rate") == 0.5

    def test_set_metric(self):
        self.mm.set_metric("performance_score", 0.95)
        assert self.mm.get_metric("performance_score") == 0.95

    def test_summary(self):
        self.mm.record_decision(correct=True)
        summary = self.mm.get_summary()
        assert "total_decisions" in summary
        assert "decision_accuracy" in summary

    def test_reset(self):
        self.mm.record_decision(correct=True)
        self.mm.reset()
        assert self.mm.get_metric("decision_accuracy") == 0.0


# ─── MetaReportGenerator Tests ───────────────────────────────────
class TestMetaReportGenerator:
    def setup_method(self):
        self.mrg = MetaReportGenerator()

    def test_generate(self):
        report = self.mrg.generate("daily", {"score": 95})
        assert report.report_id.startswith("mrep_")
        assert report.report_type == "daily"
        assert report.data["score"] == 95

    def test_add_recommendation(self):
        report = self.mrg.generate("weekly")
        report.add_recommendation("Scale up workers")
        assert len(report.recommendations) == 1

    def test_get_recent(self):
        for _ in range(3):
            self.mrg.generate("daily")
        recent = self.mrg.get_recent(2)
        assert len(recent) == 2

    def test_export_dict(self):
        report = self.mrg.generate("monthly", {"revenue": 1000})
        d = report.export_dict()
        assert "data" in d
        assert "recommendations" in d

    def test_stats(self):
        self.mrg.generate("daily")
        self.mrg.generate("weekly")
        stats = self.mrg.get_stats()
        assert stats["total"] == 2


# ─── SelfReflectionEngine Tests ──────────────────────────────────
class TestSelfReflectionEngine:
    def setup_method(self):
        self.sre = SelfReflectionEngine()

    def test_reflect(self):
        entry = self.sre.reflect("Was the decision correct?", "Yes", "Decision was optimal")
        assert entry.reflection_id.startswith("ref_")
        assert entry.insight == "Decision was optimal"

    def test_auto_reflect(self):
        entries = self.sre.auto_reflect({"quality_score": 0.8})
        assert len(entries) == 3

    def test_get_reflections(self):
        for _ in range(5):
            self.sre.reflect("Q", "A")
        reflections = self.sre.get_reflections(3)
        assert len(reflections) == 3

    def test_get_action_items(self):
        entry = self.sre.reflect("Q", "A")
        entry.action_item = "Improve hooks"
        items = self.sre.get_action_items()
        assert "Improve hooks" in items

    def test_stats(self):
        self.sre.reflect("Q", "A")
        stats = self.sre.get_stats()
        assert stats["total_reflections"] == 1


# ─── GlobalOrchestratorAPI Tests ─────────────────────────────────
class TestGlobalOrchestratorAPI:
    def setup_method(self):
        self.api = GlobalOrchestratorAPI()

    def test_register_and_execute(self):
        self.api.register("analyze", lambda ctx: {"result": "analyzed"})
        result = self.api.execute("analyze", {"topic": "AI"})
        assert result["status"] == "success"
        assert result["result"]["result"] == "analyzed"

    def test_execute_not_found(self):
        result = self.api.execute("nonexistent")
        assert result["status"] == "not_found"

    def test_execute_error(self):
        self.api.register("fail", lambda ctx: 1/0)
        result = self.api.execute("fail")
        assert result["status"] == "error"

    def test_analyze(self):
        self.api.register("analyze", lambda ctx: "ok")
        result = self.api.analyze({"topic": "AI"})
        assert result["status"] == "success"

    def test_publish(self):
        self.api.register("publish", lambda ctx: "published")
        result = self.api.publish({"content": "test"})
        assert result["status"] == "success"

    def test_shutdown(self):
        result = self.api.shutdown()
        assert result["status"] == "shutdown"

    def test_status(self):
        self.api.register("test", lambda ctx: None)
        status = self.api.status()
        assert status["handlers"] == 1

    def test_history(self):
        self.api.register("test", lambda ctx: "ok")
        self.api.execute("test")
        history = self.api.get_history()
        assert len(history) == 1


# ─── Integration Tests ───────────────────────────────────────────
class TestMetaControllerIntegration:
    def setup_method(self):
        self.mc = MetaController()
        self.gm = GoalManager()
        self.de = DecisionEngine()
        self.cm = ContextManager()
        self.op = ObjectivePlanner()
        self.ac = AICoordinator()
        self.cr = ConflictResolver()
        self.pa = PolicyArbiter()
        self.mm = MetaMetrics()

    def test_full_workflow(self):
        self.mc.start()
        goal = self.gm.create_goal("Grow followers", priority="high")
        plan = self.op.create_plan(goal.goal_id, "grow_followers")
        self.cm.update({"platform": "linkedin", "topic": "AI"})
        self.ac.coordinate_batch(["writing_ai", "quality_ai"])
        decision = self.de.decide({"quality_score": 0.85, "risk_level": "low"})
        policy = self.pa.check("Great professional post about AI!", {})
        self.mm.record_decision(correct=decision.action == "publish_now")
        self.gm.complete_goal(goal.goal_id)
        eval_result = self.mc.evaluate_system()
        assert eval_result["status"] == "running"
        assert self.gm.get_stats()["completed"] == 1
        assert self.mm._counters["total_decisions"] == 1

    def test_conflict_resolution_workflow(self):
        suggestions = {"writing_ai": "publish", "quality_ai": "revise"}
        conflict = self.cr.detect_conflict(suggestions)
        assert conflict is not None
        resolved = self.cr.resolve(conflict.conflict_id, strategy="priority")
        assert resolved.resolved is True

    def test_context_driven_decision(self):
        self.cm.update({"platform": "instagram", "topic": "fashion"})
        context = self.cm.get_all()
        decision = self.de.decide({"quality_score": 0.9, "risk_level": "low"})
        assert decision.action == "publish_now"

    def test_goal_to_plan_to_execution(self):
        goal = self.gm.create_goal("Increase engagement", target_metric="likes", target_value=1000)
        plan = self.op.create_plan(goal.goal_id, "increase_engagement")
        assert len(plan.steps) > 0
        for step in plan.steps:
            step["status"] = "completed"
        assert plan.is_complete is True

    def test_memory_and_learning(self):
        from layers.layer10_monetization.modules.ai_meta_controller.meta_memory import MetaMemory
        memory = MetaMemory()
        memory.store("lesson", "Hooks increase engagement by 30%", importance=0.9, tags=["writing"])
        memory.store("failure", "Too many hashtags reduced reach", importance=0.8, tags=["instagram"])
        results = memory.search(tag="writing")
        assert len(results) == 1
        assert results[0].importance == 0.9

    def test_reflection_and_improvement(self):
        from layers.layer10_monetization.modules.ai_meta_controller.self_reflection_engine import SelfReflectionEngine
        sre = SelfReflectionEngine()
        entries = sre.auto_reflect({"quality_score": 0.7, "platform": "x"})
        assert len(entries) == 3
        action_items = sre.get_action_items()
        assert isinstance(action_items, list)

    def test_report_generation(self):
        from layers.layer10_monetization.modules.ai_meta_controller.meta_report_generator import MetaReportGenerator
        mrg = MetaReportGenerator()
        report = mrg.generate("daily", {"decisions": 10, "accuracy": 0.9})
        report.add_recommendation("Increase automation rate")
        d = report.export_dict()
        assert d["data"]["accuracy"] == 0.9
        assert len(d["recommendations"]) == 1
