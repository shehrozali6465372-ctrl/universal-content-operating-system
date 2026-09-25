"""MonetizationOptimizer — bounded strategy suggestions and outcome tracking."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_MO_COUNTER = itertools.count(1)


class MonetizationStrategy:
    def __init__(self, strategy_type: str = "", platform: str = "") -> None:
        self.strategy_id = f"ms_{next(_MO_COUNTER)}"
        self.strategy_type = strategy_type
        self.platform = platform
        self.description = ""
        self.expected_revenue = 0.0
        self.confidence = 0.5
        self.priority = 2
        self.status = "suggested"
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"strategy_id": self.strategy_id, "type": self.strategy_type,
                "platform": self.platform, "expected_revenue": round(self.expected_revenue, 2),
                "confidence": round(self.confidence, 3), "priority": self.priority,
                "status": self.status}


class MonetizationOptimizer:
    def __init__(self, max_strategies: int = 10000) -> None:
        if max_strategies <= 0:
            raise ValueError("max_strategies must be positive")
        self._max_strategies = max_strategies
        self._strategies: List[MonetizationStrategy] = []
        self._performance: Dict[str, Dict[str, float]] = {}

    def suggest(self, strategy_type: str, platform: str,
                expected_revenue: float = 0.0, description: str = "",
                confidence: float = 0.5) -> MonetizationStrategy:
        if expected_revenue < 0 or not 0 <= confidence <= 1:
            raise ValueError("invalid strategy estimate or confidence")
        strategy = MonetizationStrategy(strategy_type, platform)
        strategy.expected_revenue, strategy.description = expected_revenue, description
        strategy.confidence = confidence
        self._strategies.append(strategy)
        if len(self._strategies) > self._max_strategies:
            self._strategies.pop(0)
        return strategy

    def get_top_strategies(self, count: int = 5, platform: str = "") -> List[MonetizationStrategy]:
        strategies = self._strategies if not platform else [
            s for s in self._strategies if s.platform == platform
        ]
        return sorted(strategies, key=lambda s: s.expected_revenue * s.confidence,
                      reverse=True)[:max(0, count)]

    def record_outcome(self, strategy_id: str, actual_revenue: float) -> bool:
        if actual_revenue < 0:
            return False
        strategy = next((s for s in self._strategies if s.strategy_id == strategy_id), None)
        if strategy is None:
            return False
        key = f"{strategy.strategy_type}:{strategy.platform}"
        data = self._performance.setdefault(key, {"total_expected": 0.0, "total_actual": 0.0, "count": 0})
        data["total_expected"] += strategy.expected_revenue
        data["total_actual"] += actual_revenue
        data["count"] += 1
        return True

    def get_accuracy(self) -> Dict[str, float]:
        return {key: round(data["total_actual"] / data["total_expected"], 3)
                if data["total_expected"] else 0.0
                for key, data in self._performance.items()}

    def get_by_platform(self, platform: str) -> List[MonetizationStrategy]:
        return [s for s in self._strategies if s.platform == platform]

    def get_by_type(self, strategy_type: str) -> List[MonetizationStrategy]:
        return [s for s in self._strategies if s.strategy_type == strategy_type]

    def get_stats(self) -> Dict[str, Any]:
        platforms: Dict[str, int] = {}
        for strategy in self._strategies:
            platforms[strategy.platform] = platforms.get(strategy.platform, 0) + 1
        return {"total_strategies": len(self._strategies), "by_platform": platforms}
