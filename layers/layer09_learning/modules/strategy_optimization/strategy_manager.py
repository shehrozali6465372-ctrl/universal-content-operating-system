"""Strategy Manager — Orchestrate the full strategy optimization pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

from layers.layer09_learning.modules.strategy_optimization.strategy_profile import StrategyProfile
from layers.layer09_learning.modules.strategy_optimization.strategy_history import StrategyHistory
from layers.layer09_learning.modules.strategy_optimization.strategy_comparator import StrategyComparator
from layers.layer09_learning.modules.strategy_optimization.strategy_patterns import StrategyPatternDetector
from layers.layer09_learning.modules.strategy_optimization.strategy_optimizer import StrategyOptimizer
from layers.layer09_learning.modules.strategy_optimization.strategy_recommender import StrategyRecommender
from layers.layer09_learning.modules.strategy_optimization.strategy_memory import StrategyMemory
from layers.layer09_learning.modules.strategy_optimization.strategy_metrics import StrategyMetrics
from layers.layer09_learning.modules.strategy_optimization.strategy_validator import StrategyValidator

_SMGR_COUNTER = itertools.count(1)


class StrategyCycleResult:
    """Result of a full strategy optimization cycle."""

    __slots__ = (
        "cycle_id", "strategy_id", "patterns_found", "optimization",
        "recommendations", "validation_score", "is_approved",
        "timestamp", "duration_ms",
    )

    def __init__(self, strategy_id: str = "") -> None:
        self.cycle_id: str = f"scy_{next(_SMGR_COUNTER)}"
        self.strategy_id = strategy_id
        self.patterns_found: int = 0
        self.optimization = None
        self.recommendations: List[Dict[str, Any]] = []
        self.validation_score: float = 0.0
        self.is_approved: bool = False
        self.timestamp: float = time.time()
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "strategy_id": self.strategy_id,
            "patterns_found": self.patterns_found,
            "recommendation_count": len(self.recommendations),
            "validation_score": round(self.validation_score, 2),
            "is_approved": self.is_approved,
            "duration_ms": round(self.duration_ms, 1),
        }


class StrategyManager:
    """Orchestrate the full strategy optimization pipeline.

    Flow: Detect Patterns → Optimize → Recommend → Validate → Store
    """

    def __init__(self) -> None:
        self.history = StrategyHistory()
        self.comparator = StrategyComparator()
        self.pattern_detector = StrategyPatternDetector()
        self.optimizer = StrategyOptimizer()
        self.recommender = StrategyRecommender()
        self.memory = StrategyMemory()
        self.metrics = StrategyMetrics()
        self.validator = StrategyValidator()
        self._strategies: List[StrategyProfile] = []
        self._cycles: List[StrategyCycleResult] = []
        self._events: List[Dict[str, Any]] = []

    def register_strategy(self, strategy: StrategyProfile) -> None:
        self._strategies.append(strategy)

    def run_optimization_cycle(self, strategy: StrategyProfile) -> StrategyCycleResult:
        start = time.time()
        result = StrategyCycleResult(strategy.strategy_id)

        # Step 1: Detect patterns across all strategies
        if strategy not in self._strategies:
            self._strategies.append(strategy)
        patterns = self.pattern_detector.detect(self._strategies)
        result.patterns_found = len(patterns)
        self.metrics.record_analysis()

        # Step 2: Optimize
        optimization = self.optimizer.optimize(strategy, patterns)
        result.optimization = optimization
        improved = optimization.changes_made > 0
        self.metrics.record_optimization(optimization.confidence, improved)

        # Step 3: Recommend
        recommendations = self.recommender.recommend(self._strategies)
        result.recommendations = [r.to_dict() for r in recommendations]
        self.metrics.record_recommendation(len(recommendations))

        # Step 4: Validate
        validation = self.validator.validate(strategy)
        result.validation_score = validation.score
        result.is_approved = validation.is_valid

        # Step 5: Store learnings
        if patterns:
            self.memory.store(
                strategy.strategy_id, "pattern_analysis",
                f"Detected {len(patterns)} patterns",
                confidence=0.7,
                tags=[strategy.strategy_type],
            )

        # Step 6: Record history
        self.history.record(
            strategy, "optimized",
            {"engagement": strategy.avg_engagement, "reach": strategy.avg_reach},
        )

        result.duration_ms = (time.time() - start) * 1000
        self._cycles.append(result)
        self._events.append({
            "event": "strategy_cycle_completed",
            "cycle_id": result.cycle_id,
            "strategy_id": strategy.strategy_id,
            "patterns": result.patterns_found,
        })
        return result

    def compare_strategies(self, baseline: StrategyProfile, candidate: StrategyProfile) -> str:
        winner = self.comparator.get_overall_winner(baseline, candidate)
        results = self.comparator.get_results()
        if results:
            self.metrics.record_comparison(
                sum(r.change_pct for r in results) / len(results)
            )
        return winner

    def get_health(self) -> Dict[str, Any]:
        return {
            "total_cycles": len(self._cycles),
            "registered_strategies": len(self._strategies),
            "history_entries": self.history.entry_count,
            "memory_stats": self.memory.get_stats(),
            "metrics": self.metrics.get_summary(),
        }

    def get_recent_cycles(self, count: int = 5) -> List[StrategyCycleResult]:
        return list(self._cycles[-count:])

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def cycle_count(self) -> int:
        return len(self._cycles)
