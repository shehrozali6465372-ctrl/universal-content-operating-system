"""Tests for Layer 3, Module 3: Reasoning Engine."""
from layers.layer03_intelligence.modules.reasoning_engine import (
    ReasoningManager, RuleEngine, DecisionEngine, DecisionOption,
    StrategySelector, Strategy, ConstraintSolver, Constraint,
    TradeoffAnalyzer, HypothesisEngine, GoalEvaluator, Goal,
    DecisionMemory, ConfidenceReasoner, ExplanationGenerator,
    DecisionGraph, DecisionNode, CounterfactualReasoner,
    ConfidenceEvolutionTracker, DecisionReplay, ReplayStore,
    MultiObjectiveOptimizer, Objective,
)


class TestRuleEngine:
    def setup_method(self):
        self.engine = RuleEngine()

    def test_add_and_evaluate(self):
        self.engine.add_simple_rule("high_engagement",
            lambda ctx: ctx.get("engagement", 0) > 0.7,
            lambda ctx: "publish")
        result = self.engine.evaluate({"engagement": 0.9})
        assert "high_engagement" in result.rules_fired
        assert result.results["high_engagement"] == "publish"

    def test_no_match(self):
        self.engine.add_simple_rule("high_engagement",
            lambda ctx: ctx.get("engagement", 0) > 0.7,
            lambda ctx: "publish")
        result = self.engine.evaluate({"engagement": 0.3})
        assert len(result.rules_fired) == 0

    def test_priority_order(self):
        self.engine.add_simple_rule("low", lambda ctx: True, lambda ctx: "low", priority=1)
        self.engine.add_simple_rule("high", lambda ctx: True, lambda ctx: "high", priority=10)
        result = self.engine.evaluate({})
        assert result.rules_fired[0] == "high"

    def test_disable_rule(self):
        self.engine.add_simple_rule("test", lambda ctx: True, lambda ctx: "ok")
        self.engine.disable_rule("test")
        result = self.engine.evaluate({})
        assert len(result.rules_fired) == 0

    def test_first_match(self):
        self.engine.add_simple_rule("a", lambda ctx: True, lambda ctx: "a")
        self.engine.add_simple_rule("b", lambda ctx: True, lambda ctx: "b")
        result = self.engine.evaluate_first_match({})
        assert result == "a"

    def test_to_dict(self):
        self.engine.add_simple_rule("test", lambda ctx: True, lambda ctx: "ok")
        d = self.engine.to_dict()
        assert d["count"] == 1


class TestDecisionEngine:
    def setup_method(self):
        self.engine = DecisionEngine()

    def test_decide_best(self):
        opts = [DecisionOption("A"), DecisionOption("B")]
        opts[0].scores = {"engagement": 0.9, "quality": 0.9}
        opts[1].scores = {"engagement": 0.3, "quality": 0.3}
        result = self.engine.decide(opts)
        assert result.chosen_option.name == "A"

    def test_decide_with_weights(self):
        self.engine.set_weights({"risk": 3.0, "engagement": 1.0})
        opts = [DecisionOption("A"), DecisionOption("B")]
        opts[0].scores = {"engagement": 0.9, "risk": 0.1}
        opts[1].scores = {"engagement": 0.5, "risk": 0.9}
        result = self.engine.decide(opts)
        assert result.chosen_option.name == "B"

    def test_decide_empty(self):
        result = self.engine.decide([])
        assert result.chosen_option is None

    def test_confidence(self):
        opts = [DecisionOption("A"), DecisionOption("B")]
        opts[0].scores = {"score": 0.9}
        opts[1].scores = {"score": 0.5}
        result = self.engine.decide(opts)
        assert result.confidence > 0.5

    def test_simple_decide(self):
        result = self.engine.decide_simple({"A": 0.9, "B": 0.5})
        assert result == "A"


class TestStrategySelector:
    def setup_method(self):
        self.selector = StrategySelector()

    def test_select_matching(self):
        self.selector.add_strategy(Strategy("aggressive", "Go big", {"risk_tolerance": "high"}))
        self.selector.add_strategy(Strategy("conservative", "Play safe", {"risk_tolerance": "low"}))
        result = self.selector.select({"risk_tolerance": "high"})
        assert result.selected.name == "aggressive"

    def test_select_no_match(self):
        self.selector.add_strategy(Strategy("s1", "", {"risk_tolerance": "high"}))
        result = self.selector.select({"risk_tolerance": "medium"})
        assert result.selected is None or result.confidence < 0.5

    def test_select_all_matching(self):
        self.selector.add_strategy(Strategy("s1", "", {"topic": "AI"}))
        self.selector.add_strategy(Strategy("s2", "", {"topic": "AI"}))
        matching = self.selector.select_all_matching({"topic": "AI"})
        assert len(matching) == 2

    def test_to_dict(self):
        self.selector.add_strategy(Strategy("s1", "desc"))
        d = self.selector.to_dict() if hasattr(self.selector, 'to_dict') else {"count": self.selector.count()}
        assert d["count"] == 1


class TestConstraintSolver:
    def setup_method(self):
        self.solver = ConstraintSolver()

    def test_all_pass(self):
        self.solver.add_simple("budget", lambda ctx: ctx.get("budget", 0) > 0)
        result = self.solver.check({"budget": 100})
        assert result.feasible is True
        assert len(result.violations) == 0

    def test_violation(self):
        self.solver.add_simple("budget", lambda ctx: ctx.get("budget", 0) > 1000)
        result = self.solver.check({"budget": 100})
        assert result.feasible is False
        assert "budget" in result.violations

    def test_warning(self):
        self.solver.add_constraint(Constraint("soft", lambda ctx: ctx.get("x", 0) > 5, "warning"))
        result = self.solver.check({"x": 3})
        assert result.feasible is True
        assert "soft" in result.warnings

    def test_to_dict(self):
        self.solver.add_simple("test", lambda ctx: True)
        result = self.solver.check({})
        d = result.to_dict()
        assert "feasible" in d


class TestTradeoffAnalyzer:
    def setup_method(self):
        self.analyzer = TradeoffAnalyzer()

    def test_analyze(self):
        result = self.analyzer.analyze({
            "A": {"cost": 0.9, "quality": 0.5},
            "B": {"cost": 0.5, "quality": 0.9},
        })
        assert result.best_option in ("A", "B")

    def test_analyze_empty(self):
        result = self.analyzer.analyze({})
        assert result.best_option == ""

    def test_weakest_dimension(self):
        result = self.analyzer.analyze({"A": {"cost": 0.9, "quality": 0.3}})
        assert result.weakest_dimension == "quality"


class TestHypothesisEngine:
    def setup_method(self):
        self.engine = HypothesisEngine()

    def test_propose_and_evaluate(self):
        h = self.engine.propose("AI will grow")
        self.engine.add_evidence_for(h, "trend data")
        self.engine.add_evidence_for(h, "competitor data")
        result = self.engine.evaluate(h)
        assert result.verdict == "supported"

    def test_refute(self):
        h = self.engine.propose("Crypto will crash")
        self.engine.add_evidence_against(h, "evidence 1")
        self.engine.add_evidence_against(h, "evidence 2")
        self.engine.add_evidence_against(h, "evidence 3")
        result = self.engine.evaluate(h)
        assert result.verdict == "refuted"

    def test_inconclusive(self):
        h = self.engine.propose("Unknown")
        result = self.engine.evaluate(h)
        assert result.verdict == "inconclusive"

    def test_count(self):
        self.engine.propose("h1")
        self.engine.propose("h2")
        assert self.engine.count() == 2


class TestGoalEvaluator:
    def setup_method(self):
        self.evaluator = GoalEvaluator()

    def test_achieved(self):
        g = Goal("test", target=100, current=100)
        result = self.evaluator.evaluate(g)
        assert result.status == "achieved"

    def test_on_track(self):
        g = Goal("test", target=100, current=80)
        result = self.evaluator.evaluate(g)
        assert result.status == "on_track"

    def test_behind(self):
        g = Goal("test", target=100, current=10)
        result = self.evaluator.evaluate(g)
        assert result.status == "behind"

    def test_overall_progress(self):
        self.evaluator.add_goal(Goal("a", 100, 50))
        self.evaluator.add_goal(Goal("b", 100, 75))
        assert self.evaluator.get_overall_progress() == 0.625


class TestDecisionMemory:
    def setup_method(self):
        self.memory = DecisionMemory()

    def test_store_and_retrieve(self):
        record = self.memory.create_and_store("d1", "publish", 0.9)
        assert self.memory.count() == 1
        assert record.chosen_option == "publish"

    def test_record_outcome(self):
        self.memory.create_and_store("d1", "publish", 0.9)
        self.memory.record_outcome("d1", "success")
        assert self.memory.get_success_rate() == 1.0

    def test_success_rate(self):
        self.memory.create_and_store("d1", "a", 0.9)
        self.memory.create_and_store("d2", "b", 0.8)
        self.memory.record_outcome("d1", "success")
        self.memory.record_outcome("d2", "failure")
        assert self.memory.get_success_rate() == 0.5

    def test_max_records_trimmed(self):
        memory = DecisionMemory(max_records=3)
        for i in range(10):
            memory.create_and_store(f"d{i}", "a", 0.5)
        assert memory.count() <= 3


class TestConfidenceReasoner:
    def setup_method(self):
        self.reasoner = ConfidenceReasoner()

    def test_high_confidence(self):
        result = self.reasoner.reason({"data": 0.9, "source": 0.8})
        assert result.overall > 0.7
        assert result.risk_level == "low"

    def test_low_confidence(self):
        result = self.reasoner.reason({"data": 0.2, "source": 0.1})
        assert result.overall < 0.4
        assert result.risk_level == "high"

    def test_empty(self):
        result = self.reasoner.reason({})
        assert result.overall == 0.0

    def test_breakdown(self):
        result = self.reasoner.reason({"a": 0.8, "b": 0.3}, {"a": 2.0, "b": 1.0})
        assert "a" in result.components
        assert result.explanation != ""


class TestExplanationGenerator:
    def setup_method(self):
        self.generator = ExplanationGenerator()

    def test_generate(self):
        exp = self.generator.generate("AI Trends", {
            "momentum": {"direction": "rising", "velocity": 0.8},
            "lifecycle": {"stage": "growing", "confidence": 0.8},
            "confidence": {"overall_confidence": 0.85, "breakdown": {"weighted_data": 0.3}},
        })
        assert exp.title == "AI Trends"
        assert len(exp.sections) > 0
        assert exp.recommendation != ""

    def test_generate_from_decision(self):
        exp = self.generator.generate_from_decision(
            "Topic", "Publish", ["Wait", "Skip"], ["High engagement"], 0.9
        )
        assert exp.confidence == 0.9

    def test_to_text(self):
        exp = self.generator.generate("Test", {"momentum": {"direction": "rising"}})
        text = exp.to_text()
        assert "Test" in text


class TestReasoningManager:
    def setup_method(self):
        self.manager = ReasoningManager()

    def test_reason_full(self):
        result = self.manager.reason("AI Jobs", {
            "options": [
                {"name": "Publish", "scores": {"engagement": 0.8, "risk": 0.3}},
                {"name": "Wait", "scores": {"engagement": 0.5, "risk": 0.1}},
            ],
            "context": {"budget": 100},
            "confidence": {"data": 0.8, "source": 0.7},
            "analysis": {"momentum": {"direction": "rising", "velocity": 0.8}},
        })
        assert result.topic == "AI Jobs"
        assert result.decision is not None
        assert result.confidence_explanation is not None

    def test_reason_minimal(self):
        result = self.manager.reason("Crypto", {})
        assert result.topic == "Crypto"

    def test_reason_batch(self):
        topics = [{"topic": "AI"}, {"topic": "Crypto"}]
        results = self.manager.reason_batch(topics)
        assert len(results) == 2

    def test_health(self):
        health = self.manager.get_health()
        assert health["status"] == "healthy"
        assert len(health["modules"]) >= 10

    def test_decision_stored_in_memory(self):
        self.manager.reason("AI", {
            "options": [{"name": "Publish", "scores": {"score": 0.9}}],
        })
        assert self.manager.decision_memory.count() >= 1


# ── Decision Graph ──────────────────────────────────────────────────

class TestDecisionGraph:
    def setup_method(self):
        self.graph = DecisionGraph()

    def test_add_node(self):
        node = DecisionNode("n1", "Research")
        node.decision = "proceed"
        node.confidence = 0.9
        self.graph.add_node(node)
        assert self.graph.count() == 1

    def test_create_node_with_deps(self):
        self.graph.create_node("n1", "Trend", confidence=0.9)
        self.graph.create_node("n2", "Score", confidence=0.8, dependencies=["n1"])
        assert self.graph.count() == 2
        deps = self.graph.get_dependencies("n2")
        assert len(deps) == 1

    def test_critical_path(self):
        self.graph.create_node("n1", "Trend", confidence=0.9)
        self.graph.create_node("n2", "Score", confidence=0.8, dependencies=["n1"])
        self.graph.create_node("n3", "Publish", confidence=0.7, dependencies=["n2"])
        path = self.graph.get_critical_path()
        assert len(path) == 3

    def test_find_weak_link(self):
        self.graph.create_node("n1", "Trend", confidence=0.9)
        self.graph.create_node("n2", "Score", confidence=0.3, dependencies=["n1"])
        self.graph.create_node("n3", "Publish", confidence=0.8, dependencies=["n2"])
        weak = self.graph.find_weak_link()
        assert weak is not None
        assert weak.node_id == "n2"

    def test_path_confidence(self):
        self.graph.create_node("n1", "Trend", confidence=0.9)
        self.graph.create_node("n2", "Score", confidence=0.8, dependencies=["n1"])
        conf = self.graph.get_path_confidence()
        assert 0.0 < conf < 1.0

    def test_to_dict(self):
        self.graph.create_node("n1", "Trend", confidence=0.9)
        d = self.graph.to_dict()
        assert "nodes" in d
        assert "edges" in d


# ── Counterfactual Reasoner ────────────────────────────────────────

class TestCounterfactualReasoner:
    def setup_method(self):
        self.reasoner = CounterfactualReasoner()

    def test_analyze(self):
        result = self.reasoner.analyze(
            {"time": "8PM", "topic": "AI"}, 0.8,
            [{"variable": "time", "values": ["10PM", "6AM"]}]
        )
        assert len(result.scenarios) > 0

    def test_best_alternative(self):
        result = self.reasoner.analyze(
            {"time": "8PM"}, 0.8,
            [{"variable": "time", "values": ["10PM", "6AM"]}]
        )
        assert result.best_alternative is not None

    def test_no_improvement(self):
        result = self.reasoner.analyze(
            {"time": "8PM"}, 0.8,
            [{"variable": "time", "values": ["8PM"]}]  # same value
        )
        assert len(result.scenarios) == 0

    def test_to_dict(self):
        result = self.reasoner.analyze(
            {"x": 5}, 0.5,
            [{"variable": "x", "values": [10]}]
        )
        d = result.to_dict()
        assert "scenarios" in d


# ── Confidence Evolution ────────────────────────────────────────────

class TestConfidenceEvolution:
    def setup_method(self):
        self.tracker = ConfidenceEvolutionTracker()

    def test_create_and_add(self):
        evo = self.tracker.create("AI")
        evo.add_stage("research", 0.9)
        evo.add_stage("writing", 0.8)
        assert evo.final_confidence > 0

    def test_weakest_stage(self):
        evo = self.tracker.create("AI")
        evo.add_stage("research", 0.9)
        evo.add_stage("writing", 0.5)
        weakest = evo.get_weakest_stage()
        assert weakest is not None
        assert weakest.stage_name == "writing"

    def test_drops(self):
        evo = self.tracker.create("AI")
        evo.add_stage("research", 0.9)
        evo.add_stage("writing", 0.5)
        drops = evo.get_drops()
        assert len(drops) > 0

    def test_tracker_add_stage(self):
        self.tracker.add_stage("AI", "research", 0.9)
        self.tracker.add_stage("AI", "writing", 0.8)
        assert self.tracker.get_final_confidence("AI") > 0

    def test_to_dict(self):
        evo = self.tracker.create("AI")
        evo.add_stage("research", 0.9)
        d = evo.to_dict()
        assert "stages" in d
        assert "final_confidence" in d


# ── Decision Replay ────────────────────────────────────────────────

class TestDecisionReplay:
    def setup_method(self):
        self.store = ReplayStore()

    def test_record_and_replay(self):
        replay = DecisionReplay("AI", "r1")
        replay.add_step("research", "proceed", 0.9)
        replay.add_step("writing", "generate", 0.85)
        replay.add_step("publish", "publish_now", 0.8)
        replay.finalize("publish_now", 0.8)
        self.store.record(replay)
        assert self.store.count() == 1

    def test_get_by_topic(self):
        self.store.record(DecisionReplay("AI", "r1"))
        self.store.record(DecisionReplay("Crypto", "r2"))
        assert len(self.store.get_by_topic("AI")) == 1

    def test_common_paths(self):
        r1 = DecisionReplay("AI", "r1")
        r1.add_step("research")
        r1.add_step("publish")
        self.store.record(r1)
        paths = self.store.get_common_paths()
        assert len(paths) > 0

    def test_to_dict(self):
        replay = DecisionReplay("AI", "r1")
        replay.add_step("research", "proceed", 0.9)
        d = replay.to_dict()
        assert "steps" in d
        assert d["step_count"] == 1

    def test_path(self):
        replay = DecisionReplay("AI", "r1")
        replay.add_step("research")
        replay.add_step("publish")
        assert replay.get_path() == "research -> publish"


# ── Multi-objective Optimizer ──────────────────────────────────────

class TestMultiObjectiveOptimizer:
    def setup_method(self):
        self.optimizer = MultiObjectiveOptimizer()
        self.optimizer.add_objective(Objective("reach", 2.0, "maximize"))
        self.optimizer.add_objective(Objective("cost", 1.0, "minimize"))

    def test_optimize(self):
        result = self.optimizer.optimize({
            "A": {"reach": 0.9, "cost": 0.3},
            "B": {"reach": 0.5, "cost": 0.1},
        })
        assert result.best_compromise is not None
        assert len(result.pareto_front) > 0

    def test_dominance(self):
        result = self.optimizer.optimize({
            "A": {"reach": 0.9, "cost": 0.1},
            "B": {"reach": 0.5, "cost": 0.5},
        })
        # A dominates B
        assert result.best_compromise.name == "A"

    def test_no_candidates(self):
        result = self.optimizer.optimize({})
        assert result.best_compromise is None

    def test_recommendations(self):
        result = self.optimizer.optimize({
            "A": {"reach": 0.9, "cost": 0.3},
        })
        assert len(result.recommendations) > 0

    def test_to_dict(self):
        result = self.optimizer.optimize({"A": {"reach": 0.9, "cost": 0.3}})
        d = result.to_dict()
        assert "pareto_front" in d
