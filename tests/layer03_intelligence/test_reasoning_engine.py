"""Tests for Module 3: Reasoning Engine."""
from layers.layer03_intelligence.modules.reasoning_engine.rule_engine import RuleEngine
from layers.layer03_intelligence.modules.reasoning_engine.decision_engine import DecisionEngine, DecisionOption
from layers.layer03_intelligence.modules.reasoning_engine.strategy_selector import StrategySelector


class TestRuleEngine:
    def setup_method(self): self.re = RuleEngine()
    def test_add_and_evaluate(self):
        self.re.add_rule("high_score", lambda ctx: ctx.get("score", 0) > 80, lambda ctx: "publish")
        results = self.re.evaluate({"score": 90})
        assert len(results) == 1
        assert results[0]["result"] == "publish"
    def test_rule_not_triggered(self):
        self.re.add_rule("high_score", lambda ctx: ctx.get("score", 0) > 80, lambda ctx: "publish")
        results = self.re.evaluate({"score": 50})
        assert results == [] or results[0]["triggered"] is False
    def test_get_triggered_rules(self):
        self.re.add_rule("r1", lambda ctx: True, lambda ctx: "ok")
        self.re.evaluate({})
        assert "r1" in self.re.get_triggered_rules()
    def test_priority_order(self):
        self.re.add_rule("low", lambda ctx: True, lambda ctx: "low", priority=1)
        self.re.add_rule("high", lambda ctx: True, lambda ctx: "high", priority=10)
        results = self.re.evaluate({})
        assert results[0]["rule"] == "high"


class TestDecisionEngine:
    def setup_method(self): self.de = DecisionEngine()
    def test_decide(self):
        opts = [
            DecisionOption("A", {"relevance": 0.9, "confidence": 0.8, "opportunity": 0.7, "risk": 0.2}),
            DecisionOption("B", {"relevance": 0.5, "confidence": 0.6, "opportunity": 0.3, "risk": 0.5}),
        ]
        best = self.de.decide(opts)
        assert best.name == "A"
    def test_rank(self):
        opts = [
            DecisionOption("low", {"relevance": 0.3}),
            DecisionOption("high", {"relevance": 0.9}),
            DecisionOption("mid", {"relevance": 0.6}),
        ]
        ranked = self.de.rank(opts)
        assert ranked[0].name == "high"
    def test_empty(self):
        assert self.de.decide([]) is None


class TestStrategySelector:
    def setup_method(self): self.ss = StrategySelector()
    def test_select(self):
        r = self.ss.select()
        assert r.name != ""
        assert r.score > 0
    def test_select_top_n(self):
        top = self.ss.select_top_n(3)
        assert len(top) == 3
        assert top[0].score >= top[1].score
    def test_add_strategy(self):
        self.ss.add_strategy("custom", {"engagement": 1.0, "reach": 1.0, "quality": 1.0})
        top = self.ss.select_top_n(1)
        assert top[0].name == "custom"
