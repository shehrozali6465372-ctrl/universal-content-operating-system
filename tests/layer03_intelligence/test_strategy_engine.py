"""Tests for Layer 3 Module 8 — Strategy Engine (production-grade)."""
import pytest
from layers.layer03_intelligence.modules.strategy_engine.strategy_generator import (
    StrategyGenerator, GeneratedStrategy,
)
from layers.layer03_intelligence.modules.strategy_engine.strategy_evaluator import (
    StrategyEvaluator, EvaluationResult,
)
from layers.layer03_intelligence.modules.strategy_engine.strategy_adapter import (
    StrategyAdapter, AdaptationResult,
)
from layers.layer03_intelligence.modules.strategy_engine.goal_planner import (
    GoalPlanner, Goal,
)
from layers.layer03_intelligence.modules.strategy_engine.risk_analyzer import (
    RiskAnalyzer, RiskAssessment,
)
from layers.layer03_intelligence.modules.strategy_engine.strategy_selector import (
    StrategySelector, SelectionResult,
)
from layers.layer03_intelligence.modules.strategy_engine.strategy_memory import (
    StrategyMemory,
)
from layers.layer03_intelligence.modules.strategy_engine.strategy_explainer import (
    StrategyExplainer, StrategyExplanation,
)
from layers.layer03_intelligence.modules.strategy_engine.strategy_manager import (
    StrategyManager, StrategyManagerResult,
)


# ── StrategyGenerator ──

class TestStrategyGenerator:
    def setup_method(self):
        self.gen = StrategyGenerator()

    def test_generate_basic(self):
        s = self.gen.generate("AI Jobs", 85.0)
        assert isinstance(s, GeneratedStrategy)
        assert s.confidence > 0
        assert len(s.goals) > 0

    def test_generate_with_trend_data(self):
        trend = {"momentum": 0.8, "virality_score": 0.9, "confidence": 0.85}
        s = self.gen.generate("Crypto", 70.0, intent="educational", trend_data=trend)
        assert s.risk_level in ("low", "medium", "high")
        assert any("momentum" in r.lower() or "Crypto" in r for r in s.reasoning)

    def test_generate_with_audience_data(self):
        audience = {"peak_hours": [8, 12, 20], "expected_engagement": 0.8, "confidence": 0.9}
        s = self.gen.generate("Health", 60.0, audience_data=audience)
        assert len(s.post_schedule) == 3
        assert s.confidence > 0

    def test_generate_with_competitor_data(self):
        competitor = {"competition_level": 0.9}
        s = self.gen.generate("AI", 50.0, competitor_data=competitor)
        assert s.risk_level == "high"

    def test_generate_long_term(self):
        s = self.gen.generate("AI", 80.0, horizon="long")
        assert s.horizon == "long"
        assert len(s.goals) >= 2

    def test_generate_medium_term(self):
        s = self.gen.generate("Tech", 70.0, horizon="medium")
        assert s.horizon == "medium"

    def test_generate_batch(self):
        topics = [
            {"topic": "AI", "score": 80},
            {"topic": "Crypto", "score": 60},
        ]
        results = self.gen.generate_batch(topics)
        assert len(results) == 2
        assert self.gen.generation_count == 2

    def test_content_mix_educational(self):
        s = self.gen.generate("AI", 80, intent="educational")
        assert "educational" in s.content_mix
        assert s.content_mix["educational"] >= 0.5

    def test_content_mix_promotional(self):
        s = self.gen.generate("AI", 80, intent="promotional")
        assert "promotional" in s.content_mix

    def test_to_dict(self):
        s = self.gen.generate("AI", 80)
        d = s.to_dict()
        assert "strategy_id" in d
        assert "confidence" in d

    def test_tactics_include_image_for_high_score(self):
        s = self.gen.generate("AI", 90)
        actions = [t["action"] for t in s.tactics]
        assert "generate_image" in actions


# ── StrategyEvaluator ──

class TestStrategyEvaluator:
    def setup_method(self):
        self.ev = StrategyEvaluator()

    def test_evaluate_basic(self):
        data = {"strategy_id": "s1", "confidence": 0.8, "risk_level": "low",
                "score": 80, "tactics": [{"effort": "low"}], "goals": [{"g": 1}]}
        r = self.ev.evaluate(data)
        assert isinstance(r, EvaluationResult)
        assert r.overall_score > 0

    def test_evaluate_grade(self):
        data = {"confidence": 0.9, "risk_level": "low", "score": 90,
                "tactics": [{"effort": "low"}], "goals": [{"g": 1}]}
        r = self.ev.evaluate(data)
        assert r.grade in ("A+", "A")

    def test_evaluate_weak_strategy(self):
        data = {"confidence": 0.2, "risk_level": "high", "score": 20,
                "tactics": [{"effort": "high"}], "goals": []}
        r = self.ev.evaluate(data)
        assert r.overall_score < 0.5

    def test_compare(self):
        e1 = EvaluationResult("s1")
        e1.overall_score = 0.8
        e1.dimensions = {"feasibility": 0.7}
        e2 = EvaluationResult("s2")
        e2.overall_score = 0.6
        e2.dimensions = {"feasibility": 0.5}
        cmp = self.ev.compare(e1, e2)
        assert cmp["winner"] == "s1"
        assert cmp["margin"] == pytest.approx(0.2, abs=0.01)

    def test_evaluate_batch(self):
        data1 = {"confidence": 0.8, "score": 80, "tactics": [], "goals": []}
        data2 = {"confidence": 0.6, "score": 60, "tactics": [], "goals": []}
        results = self.ev.evaluate_batch([data1, data2])
        assert len(results) == 2

    def test_strengths_detected(self):
        data = {"confidence": 0.9, "risk_level": "low", "score": 85,
                "tactics": [{"effort": "low"}], "goals": [{"g": 1}]}
        r = self.ev.evaluate(data)
        assert len(r.strengths) > 0

    def test_weaknesses_detected(self):
        data = {"confidence": 0.1, "risk_level": "high", "score": 15,
                "tactics": [{"effort": "high"}], "goals": []}
        r = self.ev.evaluate(data)
        assert len(r.weaknesses) > 0

    def test_to_dict(self):
        data = {"confidence": 0.8, "score": 80, "tactics": [], "goals": []}
        r = self.ev.evaluate(data)
        d = r.to_dict()
        assert "overall_score" in d
        assert "grade" in d


# ── StrategyAdapter ──

class TestStrategyAdapter:
    def setup_method(self):
        self.adapter = StrategyAdapter()

    def test_adapt_low_engagement(self):
        data = {"strategy_id": "s1", "tactics": [{"action": "write_post"}]}
        signals = {"engagement_rate": 0.1}
        r = self.adapter.adapt(data, signals=signals)
        assert isinstance(r, AdaptationResult)
        assert any(a["type"] == "increase_hook" for a in r.adaptations)

    def test_adapt_trend_decline(self):
        data = {"strategy_id": "s1", "tactics": []}
        signals = {"trend_momentum_change": -0.5}
        r = self.adapter.adapt(data, signals=signals)
        assert any(a["type"] == "pivot_topic" for a in r.adaptations)

    def test_adapt_trend_rise(self):
        data = {"strategy_id": "s1", "tactics": []}
        signals = {"trend_momentum_change": 0.6}
        r = self.adapter.adapt(data, signals=signals)
        assert any(a["type"] == "accelerate_publish" for a in r.adaptations)

    def test_adapt_competition_spike(self):
        data = {"strategy_id": "s1", "tactics": []}
        signals = {"competition_spike": True}
        r = self.adapter.adapt(data, signals=signals)
        assert any(a["type"] == "differentiate" for a in r.adaptations)

    def test_adapt_require_image_constraint(self):
        data = {"strategy_id": "s1", "tactics": [{"action": "write_post"}]}
        constraints = {"require_image": True}
        r = self.adapter.adapt(data, constraints=constraints)
        assert any(a["type"] == "add_image" for a in r.adaptations)

    def test_adapt_no_signals(self):
        data = {"strategy_id": "s1", "tactics": []}
        r = self.adapter.adapt(data)
        assert len(r.adaptations) == 0

    def test_adapt_urgency_high(self):
        data = {"strategy_id": "s1", "tactics": []}
        r = self.adapter.adapt_urgency(data, urgency=0.9)
        assert len(r.adaptations) > 0

    def test_to_dict(self):
        data = {"strategy_id": "s1", "tactics": []}
        r = self.adapter.adapt(data)
        d = r.to_dict()
        assert "strategy_id" in d

    def test_adaptation_count(self):
        self.adapter.adapt({"tactics": []})
        self.adapter.adapt({"tactics": []})
        assert self.adapter.adaptation_count == 2


# ── GoalPlanner ──

class TestGoalPlanner:
    def setup_method(self):
        self.planner = GoalPlanner()

    def test_create_goals(self):
        goals = self.planner.create_goals([
            {"name": "Write post", "priority": "high"},
            {"name": "Generate image", "priority": "medium"},
        ])
        assert len(goals) == 2
        assert goals[0].priority == "high"

    def test_plan_execution_order(self):
        g1 = Goal(name="A", priority="high")
        g2 = Goal(name="B", priority="low")
        plan = self.planner.plan([g1, g2])
        assert len(plan.execution_order) == 2

    def test_plan_with_dependencies(self):
        g1 = Goal(name="Collect data", priority="high")
        g2 = Goal(name="Write post", priority="medium")
        g2.dependencies = [g1.goal_id]
        plan = self.planner.plan([g1, g2])
        assert plan.execution_order.index(g1.goal_id) < plan.execution_order.index(g2.goal_id)

    def test_reprioritize(self):
        g1 = Goal(name="A", priority="low")
        g2 = Goal(name="B", priority="medium")
        plan = self.planner.plan([g1, g2])
        self.planner.reprioritize(plan, {g1.goal_id: "critical"})
        assert g1.priority == "critical"

    def test_update_progress(self):
        g1 = Goal(name="A")
        plan = self.planner.plan([g1])
        self.planner.update_progress(plan, g1.goal_id, 0.5)
        assert g1.progress == 0.5
        assert g1.status == "in_progress"

    def test_update_progress_complete(self):
        g1 = Goal(name="A")
        plan = self.planner.plan([g1])
        self.planner.update_progress(plan, g1.goal_id, 1.0)
        assert g1.status == "completed"

    def test_get_blocked_goals(self):
        g1 = Goal(name="A")
        g2 = Goal(name="B")
        g2.dependencies = [g1.goal_id]
        plan = self.planner.plan([g1, g2])
        blocked = self.planner.get_blocked_goals(plan)
        assert len(blocked) == 1

    def test_get_plan(self):
        g1 = Goal(name="A")
        plan = self.planner.plan([g1])
        assert self.planner.get_plan(plan.plan_id) is plan

    def test_to_dict(self):
        g1 = Goal(name="A", priority="high")
        d = g1.to_dict()
        assert "goal_id" in d
        assert "priority" in d


# ── RiskAnalyzer ──

class TestRiskAnalyzer:
    def setup_method(self):
        self.ra = RiskAnalyzer()

    def test_assess_low_risk(self):
        data = {"competition_level": 0.2, "trend_volatility": 0.2,
                "content_quality": 0.9, "audience_fit": 0.9}
        r = self.ra.assess(data)
        assert isinstance(r, RiskAssessment)
        assert r.risk_level in ("low", "medium")

    def test_assess_high_risk(self):
        data = {"competition_level": 0.95, "trend_volatility": 0.9,
                "content_quality": 0.2, "audience_fit": 0.2}
        r = self.ra.assess(data)
        assert r.risk_level == "high"

    def test_risk_factors_populated(self):
        r = self.ra.assess({})
        assert len(r.risk_factors) > 0

    def test_mitigations_for_high_risk(self):
        data = {"competition_level": 0.95, "topic_saturation": 0.9,
                "confidence_level": 0.1}
        r = self.ra.assess(data)
        assert len(r.mitigations) > 0

    def test_compare_risks(self):
        low = self.ra.assess({"competition_level": 0.1})
        high = self.ra.assess({"competition_level": 0.9})
        sorted_r = self.ra.compare_risks([high, low])
        assert sorted_r[0].overall_risk <= sorted_r[1].overall_risk

    def test_suggest_low_risk_strategy(self):
        s1 = {"competition_level": 0.1}
        s2 = {"competition_level": 0.9}
        best = self.ra.suggest_low_risk_strategy([s1, s2])
        assert best == s1

    def test_suggest_empty_list(self):
        assert self.ra.suggest_low_risk_strategy([]) is None

    def test_to_dict(self):
        r = self.ra.assess({})
        d = r.to_dict()
        assert "overall_risk" in d
        assert "risk_level" in d


# ── StrategySelector ──

class TestStrategySelector:
    def setup_method(self):
        self.sel = StrategySelector()

    def test_select_basic(self):
        c1 = {"strategy_id": "s1", "score": 80, "confidence": 0.9, "tactics": [{"effort": "low"}]}
        c2 = {"strategy_id": "s2", "score": 60, "confidence": 0.5, "tactics": [{"effort": "high"}]}
        r = self.sel.select([c1, c2])
        assert isinstance(r, SelectionResult)
        assert r.selected_id == "s1"

    def test_select_empty(self):
        r = self.sel.select([])
        assert r.selected_id == ""

    def test_ranking_order(self):
        c1 = {"score": 50, "confidence": 0.5, "tactics": []}
        c2 = {"score": 90, "confidence": 0.9, "tactics": []}
        r = self.sel.select([c1, c2])
        assert r.ranking[0]["score"] >= r.ranking[1]["score"]

    def test_select_with_constraints(self):
        c1 = {"strategy_id": "s1", "score": 30, "confidence": 0.5, "tactics": []}
        c2 = {"strategy_id": "s2", "score": 70, "confidence": 0.7, "tactics": []}
        r = self.sel.select([c1, c2], constraints={"min_score": 50})
        assert r.selected_id == "s2"

    def test_alternatives(self):
        c1 = {"score": 90, "confidence": 0.9, "tactics": []}
        c2 = {"score": 70, "confidence": 0.7, "tactics": []}
        c3 = {"score": 50, "confidence": 0.5, "tactics": []}
        r = self.sel.select([c1, c2, c3])
        assert len(r.alternatives) == 2

    def test_to_dict(self):
        c1 = {"score": 80, "confidence": 0.8, "tactics": []}
        r = self.sel.select([c1])
        d = r.to_dict()
        assert "selected" in d


# ── StrategyMemory ──

class TestStrategyMemory:
    def setup_method(self):
        self.mem = StrategyMemory(max_size=5)

    def test_store_and_get(self):
        rec = self.mem.store({"strategy_id": "s1"}, outcome="success", performance_score=0.9)
        assert rec.outcome == "success"
        assert self.mem.size == 1

    def test_get_by_strategy(self):
        self.mem.store({"strategy_id": "s1"}, outcome="success")
        self.mem.store({"strategy_id": "s1"}, outcome="failure")
        results = self.mem.get_by_strategy("s1")
        assert len(results) == 2

    def test_get_successful(self):
        self.mem.store({}, outcome="success", performance_score=0.8)
        self.mem.store({}, outcome="failure", performance_score=0.2)
        assert len(self.mem.get_successful()) == 1

    def test_get_failed(self):
        self.mem.store({}, outcome="failure")
        self.mem.store({}, outcome="success")
        assert len(self.mem.get_failed()) == 1

    def test_max_size_eviction(self):
        for i in range(7):
            self.mem.store({"strategy_id": f"s{i}"})
        assert self.mem.size == 5

    def test_get_similar(self):
        self.mem.store({}, tags=["AI", "tech"])
        self.mem.store({}, tags=["AI", "science"])
        self.mem.store({}, tags=["cooking"])
        similar = self.mem.get_similar(["AI"])
        assert len(similar) == 2

    def test_get_lessons(self):
        self.mem.store({}, outcome="failure", lessons=["Use better hooks"])
        lessons = self.mem.get_lessons()
        assert "Use better hooks" in lessons

    def test_stats(self):
        self.mem.store({}, outcome="success", performance_score=0.9)
        self.mem.store({}, outcome="failure", performance_score=0.2)
        s = self.mem.stats()
        assert s["total"] == 2
        assert s["success_rate"] == 0.5

    def test_stats_empty(self):
        s = self.mem.stats()
        assert s["total"] == 0

    def test_clear(self):
        self.mem.store({})
        self.mem.clear()
        assert self.mem.size == 0

    def test_to_dict(self):
        rec = self.mem.store({"strategy_id": "s1"})
        d = rec.to_dict()
        assert "record_id" in d


# ── StrategyExplainer ──

class TestStrategyExplainer:
    def setup_method(self):
        self.exp = StrategyExplainer()

    def test_explain_basic(self):
        data = {"strategy_id": "s1", "name": "test", "horizon": "short",
                "confidence": 0.8, "reasoning": ["High score"]}
        r = self.exp.explain(data)
        assert isinstance(r, StrategyExplanation)
        assert len(r.summary) > 0
        assert len(r.why_this) > 0

    def test_explain_with_risk(self):
        data = {"strategy_id": "s1", "confidence": 0.8}
        risk = {"risk_level": "high", "overall_risk": 0.7,
                "risk_factors": [{"factor": "competition", "level": "high"}]}
        r = self.exp.explain(data, risk_data=risk)
        assert any("risk" in ri.lower() for ri in r.risks)

    def test_explain_selection(self):
        sel = {"selected": "s1", "ranking": [{"rank": 1}], "reasoning": ["Higher score"]}
        text = self.exp.explain_selection(sel)
        assert "s1" in text

    def test_explain_risk(self):
        risk = {"risk_level": "low", "overall_risk": 0.2, "mitigations": []}
        text = self.exp.explain_risk(risk)
        assert "low" in text

    def test_to_dict(self):
        data = {"confidence": 0.8, "reasoning": ["test"]}
        r = self.exp.explain(data)
        d = r.to_dict()
        assert "summary" in d
        assert "sections" in d


# ── StrategyManager (orchestrator) ──

class TestStrategyManager:
    def setup_method(self):
        self.mgr = StrategyManager()

    def test_run_pipeline_basic(self):
        result = self.mgr.run_pipeline("AI Jobs", score=85.0)
        assert isinstance(result, StrategyManagerResult)
        assert result.topic == "AI Jobs"
        assert result.selected_strategy is not None
        assert result.pipeline_time_ms > 0

    def test_run_pipeline_with_goals(self):
        goals = [{"name": "Write post", "priority": "high"}]
        result = self.mgr.run_pipeline("Crypto", score=70.0, goal_configs=goals)
        assert result.goal_plan is not None
        assert result.goal_plan.goal_count == 1

    def test_run_pipeline_with_all_data(self):
        result = self.mgr.run_pipeline(
            "AI",
            score=90,
            intent="educational",
            trend_data={"momentum": 0.8},
            audience_data={"peak_hours": [9, 18], "expected_engagement": 0.7},
            competitor_data={"competition_level": 0.3},
            content_data={"quality_score": 0.85},
        )
        assert result.explanation is not None
        assert result.risk_assessment is not None

    def test_run_pipeline_generates_strategies(self):
        result = self.mgr.run_pipeline("AI", score=80)
        assert len(result.all_strategies) >= 3

    def test_adapt_strategy(self):
        data = {"strategy_id": "s1", "tactics": []}
        r = self.mgr.adapt_strategy(data, signals={"engagement_rate": 0.1})
        assert r is not None

    def test_memory_stats(self):
        self.mgr.run_pipeline("AI", score=80)
        stats = self.mgr.get_memory_stats()
        assert stats["total"] >= 1

    def test_pipeline_count(self):
        self.mgr.run_pipeline("AI", score=80)
        self.mgr.run_pipeline("Crypto", score=70)
        assert self.mgr.pipeline_count == 2

    def test_get_lessons(self):
        self.mgr.run_pipeline("AI", score=80)
        lessons = self.mgr.get_lessons("AI")
        assert isinstance(lessons, list)

    def test_result_to_dict(self):
        result = self.mgr.run_pipeline("AI", score=80)
        d = result.to_dict()
        assert "topic" in d
        assert "selected" in d
        assert "pipeline_time_ms" in d
