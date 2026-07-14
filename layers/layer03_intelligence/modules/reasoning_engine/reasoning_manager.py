"""Reasoning Manager - Orchestrator for Reasoning Engine Module."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer03_intelligence.modules.reasoning_engine.rule_engine import RuleEngine
from layers.layer03_intelligence.modules.reasoning_engine.decision_engine import (
    DecisionEngine, DecisionOption, DecisionResult,
)
from layers.layer03_intelligence.modules.reasoning_engine.strategy_selector import (
    StrategySelector, StrategyResult,
)
from layers.layer03_intelligence.modules.reasoning_engine.constraint_solver import (
    ConstraintSolver, ConstraintResult,
)
from layers.layer03_intelligence.modules.reasoning_engine.tradeoff_analyzer import TradeoffAnalyzer
from layers.layer03_intelligence.modules.reasoning_engine.hypothesis_engine import HypothesisEngine
from layers.layer03_intelligence.modules.reasoning_engine.goal_evaluator import GoalEvaluator
from layers.layer03_intelligence.modules.reasoning_engine.decision_memory import DecisionMemory
from layers.layer03_intelligence.modules.reasoning_engine.confidence_reasoner import ConfidenceReasoner
from layers.layer03_intelligence.modules.reasoning_engine.explanation_generator import ExplanationGenerator


class ReasoningResult:
    """Combined result from all reasoning sub-modules."""
    __slots__ = ("topic", "decision", "strategy", "constraints", "tradeoff",
                 "hypothesis", "confidence_explanation", "explanation",
                 "recommendation", "timestamp")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.decision: Optional[DecisionResult] = None
        self.strategy: Optional[StrategyResult] = None
        self.constraints: Optional[ConstraintResult] = None
        self.tradeoff: Optional[Any] = None
        self.hypothesis: Optional[Any] = None
        self.confidence_explanation: Optional[Any] = None
        self.explanation: Optional[Any] = None
        self.recommendation = ""
        self.timestamp = time.time()

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "decision": self.decision.to_dict() if self.decision else None,
            "strategy": self.strategy.to_dict() if self.strategy else None,
            "constraints": self.constraints.to_dict() if self.constraints else None,
            "tradeoff": self.tradeoff.to_dict() if self.tradeoff else None,
            "hypothesis": self.hypothesis.to_dict() if self.hypothesis else None,
            "confidence_explanation": self.confidence_explanation.to_dict() if self.confidence_explanation else None,
            "explanation": self.explanation.to_dict() if self.explanation else None,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }


class ReasoningManager:
    """Main orchestrator for the Reasoning Engine.

    Usage::

        manager = ReasoningManager()
        result = manager.reason("AI Jobs Trend", {
            "options": [{"name": "Publish", "scores": {"engagement": 0.8, "risk": 0.3}},
                        {"name": "Wait", "scores": {"engagement": 0.5, "risk": 0.1}}],
            "context": {"budget": 100, "deadline": "2026-08-01"},
        })
    """

    def __init__(self) -> None:
        self.rule_engine = RuleEngine()
        self.decision_engine = DecisionEngine()
        self.strategy_selector = StrategySelector()
        self.constraint_solver = ConstraintSolver()
        self.tradeoff_analyzer = TradeoffAnalyzer()
        self.hypothesis_engine = HypothesisEngine()
        self.goal_evaluator = GoalEvaluator()
        self.decision_memory = DecisionMemory()
        self.confidence_reasoner = ConfidenceReasoner()
        self.explanation_generator = ExplanationGenerator()

    def reason(self, topic: str, data: Dict) -> ReasoningResult:
        result = ReasoningResult(topic)

        # Decision making
        options_data = data.get("options", [])
        if options_data:
            options = [DecisionOption(o.get("name", ""), o.get("metadata", {}))
                       for o in options_data]
            for opt, od in zip(options, options_data):
                opt.scores = od.get("scores", {})
            weights = data.get("weights", {})
            if weights:
                self.decision_engine.set_weights(weights)
            result.decision = self.decision_engine.decide(options)

            # Store in memory
            if result.decision.chosen_option:
                self.decision_memory.create_and_store(
                    f"{topic}_{int(time.time())}",
                    result.decision.chosen_option.name,
                    result.decision.confidence,
                    {"topic": topic},
                )

        # Strategy selection
        context = data.get("context", {})
        if context:
            result.strategy = self.strategy_selector.select(context)

        # Constraint checking
        if context:
            result.constraints = self.constraint_solver.check(context)

        # Tradeoff analysis
        if options_data:
            option_scores = {o.get("name", ""): o.get("scores", {}) for o in options_data}
            result.tradeoff = self.tradeoff_analyzer.analyze(option_scores)

        # Confidence reasoning
        confidence_components = data.get("confidence", {})
        if confidence_components:
            result.confidence_explanation = self.confidence_reasoner.reason(confidence_components)

        # Explanation
        analysis = data.get("analysis", {})
        if analysis:
            result.explanation = self.explanation_generator.generate(topic, analysis)
            result.recommendation = result.explanation.recommendation

        return result

    def reason_batch(self, topics: List[Dict]) -> List[ReasoningResult]:
        return [self.reason(t.get("topic", ""), t) for t in topics]

    def get_health(self) -> Dict:
        return {
            "modules": [
                "RuleEngine", "DecisionEngine", "StrategySelector",
                "ConstraintSolver", "TradeoffAnalyzer", "HypothesisEngine",
                "GoalEvaluator", "DecisionMemory", "ConfidenceReasoner",
                "ExplanationGenerator",
            ],
            "status": "healthy",
            "rules_count": self.rule_engine.count(),
            "strategies_count": self.strategy_selector.count(),
            "constraints_count": self.constraint_solver.count(),
            "hypotheses_count": self.hypothesis_engine.count(),
            "goals_count": self.goal_evaluator.count(),
            "decisions_stored": self.decision_memory.count(),
            "success_rate": round(self.decision_memory.get_success_rate(), 3),
        }
