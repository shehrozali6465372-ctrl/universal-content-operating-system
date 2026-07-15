"""Strategy Adapter — Adapt strategy based on real-time signals."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class AdaptationResult:
    """Result of strategy adaptation."""
    __slots__ = ("strategy_id", "original_tactics", "adapted_tactics",
                 "adaptations", "reasoning", "confidence_delta", "timestamp")

    def __init__(self, strategy_id: str = "") -> None:
        self.strategy_id = strategy_id
        self.original_tactics: List[Dict[str, Any]] = []
        self.adapted_tactics: List[Dict[str, Any]] = []
        self.adaptations: List[Dict[str, str]] = []
        self.reasoning: List[str] = []
        self.confidence_delta = 0.0
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "adaptations": self.adaptations,
            "confidence_delta": round(self.confidence_delta, 4),
            "original_count": len(self.original_tactics),
            "adapted_count": len(self.adapted_tactics),
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
        }


class StrategyAdapter:
    """Adapts strategies based on real-time performance signals."""

    def __init__(self) -> None:
        self._adaptation_count = 0

    def adapt(
        self,
        strategy_data: Dict[str, Any],
        signals: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> AdaptationResult:
        """Adapt a strategy based on real-time signals."""
        result = AdaptationResult(strategy_id=strategy_data.get("strategy_id", ""))
        result.original_tactics = list(strategy_data.get("tactics", []))
        result.adapted_tactics = list(result.original_tactics)

        if not signals:
            signals = {}
        if not constraints:
            constraints = {}

        # Engagement signal adaptation
        if "engagement_rate" in signals:
            engagement = signals["engagement_rate"]
            if engagement < 0.3:
                result.adaptations.append({"type": "increase_hook", "reason": "low engagement detected"})
                result.reasoning.append(f"Engagement {engagement:.2f} below threshold — strengthening hooks")
                result.confidence_delta -= 0.05

        # Trend signal adaptation
        trend_change = signals.get("trend_momentum_change", 0)
        if trend_change < -0.3:
            result.adaptations.append({"type": "pivot_topic", "reason": "trend declining"})
            result.reasoning.append(f"Trend momentum dropped {trend_change:.2f} — consider topic pivot")
            result.confidence_delta -= 0.1
        elif trend_change > 0.3:
            result.adaptations.append({"type": "accelerate_publish", "reason": "trend rising"})
            result.reasoning.append(f"Trend rising +{trend_change:.2f} — prioritize immediate publish")
            result.confidence_delta += 0.05

        # Competition signal
        competition_spike = signals.get("competition_spike", False)
        if competition_spike:
            result.adaptations.append({"type": "differentiate", "reason": "competitor activity spike"})
            result.reasoning.append("Competitor spike detected — shift to differentiated content")
            result.confidence_delta -= 0.03

        # Constraint-based adaptation
        max_tactics = constraints.get("max_tactics", 10)
        if len(result.adapted_tactics) > max_tactics:
            result.adapted_tactics = result.adapted_tactics[:max_tactics]
            result.adaptations.append({"type": "truncate_tactics", "reason": "constraint limit"})

        force_image = constraints.get("require_image", False)
        has_image = any(t.get("action") == "generate_image" for t in result.adapted_tactics)
        if force_image and not has_image:
            result.adapted_tactics.append({"action": "generate_image", "priority": "HIGH", "effort": "low"})
            result.adaptations.append({"type": "add_image", "reason": "image required by constraint"})

        self._adaptation_count += 1
        return result

    def adapt_urgency(
        self, strategy_data: Dict[str, Any], urgency: float
    ) -> AdaptationResult:
        """Adapt strategy based on urgency level (0-1)."""
        signals: Dict[str, Any] = {}
        if urgency > 0.8:
            signals["trend_momentum_change"] = 0.5
        elif urgency < 0.3:
            signals["engagement_rate"] = 0.1
        return self.adapt(strategy_data, signals=signals)

    @property
    def adaptation_count(self) -> int:
        return self._adaptation_count
