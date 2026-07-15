"""Strategy Manager — Central orchestrator for Strategy Engine Module."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer03_intelligence.modules.strategy_engine.strategy_generator import StrategyGenerator
from layers.layer03_intelligence.modules.strategy_engine.strategy_evaluator import StrategyEvaluator
from layers.layer03_intelligence.modules.strategy_engine.strategy_adapter import StrategyAdapter
from layers.layer03_intelligence.modules.strategy_engine.goal_planner import GoalPlanner
from layers.layer03_intelligence.modules.strategy_engine.risk_analyzer import RiskAnalyzer
from layers.layer03_intelligence.modules.strategy_engine.strategy_selector import StrategySelector
from layers.layer03_intelligence.modules.strategy_engine.strategy_memory import StrategyMemory
from layers.layer03_intelligence.modules.strategy_engine.strategy_explainer import StrategyExplainer


class StrategyManagerResult:
    """Result from the Strategy Manager pipeline."""
    __slots__ = ("topic", "selected_strategy", "evaluation", "risk_assessment",
                 "goal_plan", "explanation", "adaptations", "timestamp",
                 "pipeline_time_ms", "all_strategies", "memory_stats")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.selected_strategy = None
        self.evaluation = None
        self.risk_assessment = None
        self.goal_plan = None
        self.explanation = None
        self.adaptations: List[Any] = []
        self.timestamp = time.time()
        self.pipeline_time_ms = 0.0
        self.all_strategies: List[Any] = []
        self.memory_stats: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "selected": self.selected_strategy.to_dict() if self.selected_strategy else None,
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
            "risk": self.risk_assessment.to_dict() if self.risk_assessment else None,
            "goal_plan": self.goal_plan.to_dict() if self.goal_plan else None,
            "explanation": self.explanation.to_dict() if self.explanation else None,
            "adaptations_count": len(self.adaptations),
            "pipeline_time_ms": round(self.pipeline_time_ms, 2),
            "strategies_generated": len(self.all_strategies),
            "memory_stats": self.memory_stats,
            "timestamp": self.timestamp,
        }


class StrategyManager:
    """Central orchestrator for the Strategy Engine.

    Pipeline: generate → evaluate → risk-assess → select → explain → store
    """

    def __init__(
        self,
        generator: Optional[StrategyGenerator] = None,
        evaluator: Optional[StrategyEvaluator] = None,
        adapter: Optional[StrategyAdapter] = None,
        goal_planner: Optional[GoalPlanner] = None,
        risk_analyzer: Optional[RiskAnalyzer] = None,
        selector: Optional[StrategySelector] = None,
        memory: Optional[StrategyMemory] = None,
        explainer: Optional[StrategyExplainer] = None,
    ) -> None:
        self.generator = generator or StrategyGenerator()
        self.evaluator = evaluator or StrategyEvaluator()
        self.adapter = adapter or StrategyAdapter()
        self.goal_planner = goal_planner or GoalPlanner()
        self.risk_analyzer = risk_analyzer or RiskAnalyzer()
        self.selector = selector or StrategySelector()
        self.memory = memory or StrategyMemory()
        self.explainer = explainer or StrategyExplainer()
        self._pipeline_count = 0

    def run_pipeline(
        self,
        topic: str,
        score: float = 50.0,
        intent: str = "educational",
        trend_data: Optional[Dict] = None,
        audience_data: Optional[Dict] = None,
        competitor_data: Optional[Dict] = None,
        content_data: Optional[Dict] = None,
        horizon: str = "short",
        goal_configs: Optional[List[Dict]] = None,
    ) -> StrategyManagerResult:
        """Run the full strategy pipeline."""
        start = time.time()
        result = StrategyManagerResult(topic=topic)

        # 1. Generate candidate strategies
        primary = self.generator.generate(
            topic=topic, score=score, intent=intent,
            trend_data=trend_data, audience_data=audience_data,
            competitor_data=competitor_data, content_data=content_data,
            horizon=horizon,
        )
        # Generate alternatives
        alt1 = self.generator.generate(topic=topic, score=score, intent="entertaining", horizon=horizon)
        alt2 = self.generator.generate(topic=topic, score=score, intent="inspiring", horizon=horizon)
        candidates = [primary, alt1, alt2]
        result.all_strategies = candidates

        # 2. Evaluate each
        evaluations = []
        for c in candidates:
            eval_r = self.evaluator.evaluate(c.to_dict())
            evaluations.append(eval_r)

        # 3. Risk assess
        risk_assessments = []
        for c in candidates:
            risk_data = c.to_dict()
            risk_data["risk_score"] = (1.0 - c.confidence) * 100
            ra = self.risk_analyzer.assess(risk_data)
            risk_assessments.append(ra)

        # 4. Select best
        sel_candidates = []
        for i, c in enumerate(candidates):
            sel_candidates.append({
                **c.to_dict(),
                "score": score,
                "risk_score": risk_assessments[i].risk_score if i < len(risk_assessments) else 50,
            })

        selection = self.selector.select(sel_candidates)
        result.selected_strategy = primary  # default
        for c in candidates:
            if c.strategy_id == selection.selected_id:
                result.selected_strategy = c
                break
        result.evaluation = evaluations[0] if evaluations else None
        result.risk_assessment = risk_assessments[0] if risk_assessments else None

        # 5. Goal plan
        if goal_configs:
            goals = self.goal_planner.create_goals(goal_configs)
            result.goal_plan = self.goal_planner.plan(goals)

        # 6. Adapt
        adapt_result = self.adapter.adapt(result.selected_strategy.to_dict())
        result.adaptations = [adapt_result]

        # 7. Explain
        eval_dict = evaluations[0].to_dict() if evaluations else {}
        risk_dict = risk_assessments[0].to_dict() if risk_assessments else {}
        result.explanation = self.explainer.explain(
            result.selected_strategy.to_dict(), eval_data=eval_dict, risk_data=risk_dict
        )

        # 8. Store in memory
        self.memory.store(
            result.selected_strategy.to_dict(),
            outcome="planned",
            performance_score=score / 100.0,
            lessons=[],
            tags=[topic, intent, horizon],
        )
        result.memory_stats = self.memory.stats()

        elapsed = (time.time() - start) * 1000
        result.pipeline_time_ms = elapsed
        self._pipeline_count += 1
        return result

    def adapt_strategy(
        self, strategy_data: Dict[str, Any],
        signals: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Adapt an existing strategy."""
        return self.adapter.adapt(strategy_data, signals=signals, constraints=constraints)

    def get_memory_stats(self) -> Dict[str, Any]:
        return self.memory.stats()

    def get_lessons(self, topic: str = "") -> List[str]:
        return self.memory.get_lessons(topic=topic)

    @property
    def pipeline_count(self) -> int:
        return self._pipeline_count
