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
from layers.layer03_intelligence.modules.reasoning_engine.decision_graph import DecisionGraph
from layers.layer03_intelligence.modules.reasoning_engine.counterfactual_reasoner import CounterfactualReasoner
from layers.layer03_intelligence.modules.reasoning_engine.confidence_evolution import ConfidenceEvolutionTracker
from layers.layer03_intelligence.modules.reasoning_engine.decision_replay import DecisionReplay, ReplayStore
from layers.layer03_intelligence.modules.reasoning_engine.multi_objective_optimizer import MultiObjectiveOptimizer, Objective


class ReasoningResult:
    """Combined result from all reasoning sub-modules."""
    __slots__ = ("topic", "decision", "strategy", "constraints", "tradeoff",
                 "hypothesis", "confidence_explanation", "explanation",
                 "counterfactual", "confidence_evolution", "replay",
                 "multi_objective", "recommendation", "timestamp")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.decision: Optional[DecisionResult] = None
        self.strategy: Optional[StrategyResult] = None
        self.constraints: Optional[ConstraintResult] = None
        self.tradeoff: Optional[Any] = None
        self.hypothesis: Optional[Any] = None
        self.confidence_explanation: Optional[Any] = None
        self.explanation: Optional[Any] = None
        self.counterfactual: Optional[Any] = None
        self.confidence_evolution: Optional[Any] = None
        self.replay: Optional[Any] = None
        self.multi_objective: Optional[Any] = None
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
            "counterfactual": self.counterfactual.to_dict() if self.counterfactual else None,
            "confidence_evolution": self.confidence_evolution.to_dict() if self.confidence_evolution else None,
            "replay": self.replay.to_dict() if self.replay else None,
            "multi_objective": self.multi_objective.to_dict() if self.multi_objective else None,
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
        self.decision_graph = DecisionGraph()
        self.counterfactual = CounterfactualReasoner()
        self.confidence_tracker = ConfidenceEvolutionTracker()
        self.replay_store = ReplayStore()
        self.multi_objective = MultiObjectiveOptimizer()

    def reason(self, topic: str, data: Dict) -> ReasoningResult:
        result = ReasoningResult(topic)
        import time as _time
        replay = DecisionReplay(topic, f"replay_{int(_time.time())}")

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
            replay.add_step("decision", result.decision.chosen_option.name if result.decision else "",
                           result.decision.confidence if result.decision else 0,
                           duration_ms=0)
            if result.decision.chosen_option:
                self.decision_memory.create_and_store(
                    f"{topic}_{int(_time.time())}",
                    result.decision.chosen_option.name,
                    result.decision.confidence, {"topic": topic})

        # Strategy selection
        context = data.get("context", {})
        if context:
            result.strategy = self.strategy_selector.select(context)
            replay.add_step("strategy",
                           result.strategy.selected.name if result.strategy and result.strategy.selected else "",
                           result.strategy.confidence if result.strategy else 0)

        # Constraint checking
        if context:
            result.constraints = self.constraint_solver.check(context)
            replay.add_step("constraints", "feasible" if result.constraints.feasible else "infeasible",
                           1.0 if result.constraints.feasible else 0.0)

        # Tradeoff analysis
        if options_data:
            option_scores = {o.get("name", ""): o.get("scores", {}) for o in options_data}
            result.tradeoff = self.tradeoff_analyzer.analyze(option_scores)

        # Multi-objective optimization
        objectives_data = data.get("objectives", [])
        if objectives_data and options_data:
            for obj_data in objectives_data:
                self.multi_objective.add_objective(Objective(
                    obj_data.get("name", ""), obj_data.get("weight", 1.0),
                    obj_data.get("direction", "maximize")))
            candidates = {o.get("name", ""): o.get("scores", {}) for o in options_data}
            result.multi_objective = self.multi_objective.optimize(candidates)

        # Counterfactual reasoning
        what_ifs = data.get("what_ifs", [])
        if what_ifs and data.get("context"):
            result.counterfactual = self.counterfactual.analyze(
                data["context"], result.decision.chosen_option.overall_score if result.decision and result.decision.chosen_option else 0.5,
                what_ifs)

        # Confidence reasoning
        confidence_components = data.get("confidence", {})
        if confidence_components:
            result.confidence_explanation = self.confidence_reasoner.reason(confidence_components)

        # Confidence evolution
        evo = self.confidence_tracker.create(topic)
        if result.decision and result.decision.chosen_option:
            evo.add_stage("decision", result.decision.confidence)
        if result.strategy:
            evo.add_stage("strategy", result.strategy.confidence)
        if result.confidence_explanation:
            evo.add_stage("confidence", result.confidence_explanation.overall)
        result.confidence_evolution = evo

        # Decision graph
        nodes = data.get("graph_nodes", [])
        for nd in nodes:
            self.decision_graph.create_node(
                nd.get("id", ""), nd.get("label", ""),
                nd.get("decision", ""), nd.get("confidence", 0),
                nd.get("stage", ""), nd.get("dependencies", []))
        result.replay = replay

        # Explanation
        analysis = data.get("analysis", {})
        if analysis:
            result.explanation = self.explanation_generator.generate(topic, analysis)
            result.recommendation = result.explanation.recommendation

        # Store replay
        self.replay_store.record(replay)

        return result

    def get_health(self) -> Dict:
        return {
            "modules": [
                "RuleEngine", "DecisionEngine", "StrategySelector",
                "ConstraintSolver", "TradeoffAnalyzer", "HypothesisEngine",
                "GoalEvaluator", "DecisionMemory", "ConfidenceReasoner",
                "ExplanationGenerator", "DecisionGraph", "CounterfactualReasoner",
                "ConfidenceEvolutionTracker", "ReplayStore", "MultiObjectiveOptimizer",
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

    def reason_batch(self, topics: List[Dict]) -> List[ReasoningResult]:
        return [self.reason(t.get("topic", ""), t) for t in topics]
