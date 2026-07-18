"""MonetizationOptimizer — Optimize monetization strategies."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_MO_COUNTER = itertools.count(1)


class MonetizationStrategy:
    """A monetization strategy with expected outcomes."""

    __slots__ = ("strategy_id", "strategy_type", "platform", "description",
                 "expected_revenue", "confidence", "priority", "status",
                 "created_at")

    def __init__(self, strategy_type: str = "", platform: str = "") -> None:
        self.strategy_id: str = f"ms_{next(_MO_COUNTER)}"
        self.strategy_type = strategy_type
        self.platform = platform
        self.description: str = ""
        self.expected_revenue: float = 0.0
        self.confidence: float = 0.5
        self.priority: int = 2
        self.status: str = "suggested"
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"strategy_id": self.strategy_id, "type": self.strategy_type,
                "platform": self.platform, "expected_revenue": round(self.expected_revenue, 2),
                "confidence": round(self.confidence, 3), "priority": self.priority}


class MonetizationOptimizer:
    """Optimize ad placement, affiliate, sponsorship, and pricing strategies."""

    def __init__(self) -> None:
        self._strategies: List[MonetizationStrategy] = []
        self._performance: Dict[str, Dict[str, float]] = {}

    def suggest(self, strategy_type: str, platform: str,
                expected_revenue: float = 0.0,
                description: str = "") -> MonetizationStrategy:
        strategy = MonetizationStrategy(strategy_type, platform)
        strategy.expected_revenue = expected_revenue
        strategy.description = description
        self._strategies.append(strategy)
        return strategy

    def get_top_strategies(self, count: int = 5,
                           platform: str = "") -> List[MonetizationStrategy]:
        strategies = self._strategies
        if platform:
            strategies = [s for s in strategies if s.platform == platform]
        return sorted(strategies, key=lambda s: s.expected_revenue * s.confidence,
                       reverse=True)[:count]

    def record_outcome(self, strategy_id: str, actual_revenue: float) -> bool:
        strategy = next((s for s in self._strategies
                         if s.strategy_id == strategy_id), None)
        if strategy is None:
            return False
        key = f"{strategy.strategy_type}:{strategy.platform}"
        if key not in self._performance:
            self._performance[key] = {"total_expected": 0.0, "total_actual": 0.0, "count": 0}
        self._performance[key]["total_expected"] += strategy.expected_revenue
        self._performance[key]["total_actual"] += actual_revenue
        self._performance[key]["count"] += 1
        return True

    def get_accuracy(self) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for key, data in self._performance.items():
            if data["count"] > 0:
                result[key] = round(data["total_actual"] / max(1, data["total_expected"]), 3)
        return result

    def get_by_platform(self, platform: str) -> List[MonetizationStrategy]:
        return [s for s in self._strategies if s.platform == platform]

    def get_by_type(self, strategy_type: str) -> List[MonetizationStrategy]:
        return [s for s in self._strategies if s.strategy_type == strategy_type]

    def get_stats(self) -> Dict[str, Any]:
        platforms: Dict[str, int] = {}
        for s in self._strategies:
            platforms[s.platform] = platforms.get(s.platform, 0) + 1
        return {"total_strategies": len(self._strategies), "by_platform": platforms}
