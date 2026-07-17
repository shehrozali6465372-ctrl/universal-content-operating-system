"""Strategy Optimizer — Generate optimized strategy suggestions."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import itertools

from layers.layer09_learning.modules.strategy_optimization.strategy_profile import StrategyProfile
from layers.layer09_learning.modules.strategy_optimization.strategy_patterns import StrategyPattern

_SO_COUNTER = itertools.count(1)


class StrategySuggestion:
    """A single suggestion for strategy improvement."""

    __slots__ = ("suggestion_id", "suggestion_type", "priority",
                 "field", "current_value", "suggested_value",
                 "reason", "estimated_impact")

    def __init__(self, suggestion_type: str = "targeting", priority: str = "medium") -> None:
        self.suggestion_id: str = f"ss_{next(_SO_COUNTER)}"
        self.suggestion_type = suggestion_type
        self.priority = priority
        self.field: str = ""
        self.current_value: str = ""
        self.suggested_value: str = ""
        self.reason: str = ""
        self.estimated_impact: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "suggestion_type": self.suggestion_type,
            "priority": self.priority,
            "field": self.field,
            "suggested_value": self.suggested_value,
            "reason": self.reason,
            "estimated_impact": self.estimated_impact,
        }


class StrategyOptimizationResult:
    """Result of optimizing a strategy."""

    __slots__ = ("strategy_id", "suggestions", "confidence", "changes_made")

    def __init__(self, strategy_id: str = "") -> None:
        self.strategy_id = strategy_id
        self.suggestions: List[StrategySuggestion] = []
        self.confidence: float = 0.0
        self.changes_made: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "suggestion_count": len(self.suggestions),
            "confidence": round(self.confidence, 3),
            "changes_made": self.changes_made,
        }


class StrategyOptimizer:
    """Generate optimization suggestions for content strategies."""

    def __init__(self) -> None:
        self._results: List[StrategyOptimizationResult] = []

    def optimize(
        self,
        strategy: StrategyProfile,
        patterns: Optional[List[StrategyPattern]] = None,
    ) -> StrategyOptimizationResult:
        result = StrategyOptimizationResult(strategy.strategy_id)
        suggestions = []
        suggestions.extend(self._suggest_targeting(strategy))
        suggestions.extend(self._suggest_frequency(strategy))
        suggestions.extend(self._suggest_content_pillars(strategy))
        suggestions.extend(self._suggest_engagement_tactics(strategy))
        if patterns:
            suggestions.extend(self._suggest_from_patterns(strategy, patterns))
        result.suggestions = suggestions
        result.changes_made = len(suggestions)
        result.confidence = self._compute_confidence(strategy, suggestions)
        self._results.append(result)
        return result

    def _suggest_targeting(self, s: StrategyProfile) -> List[StrategySuggestion]:
        suggestions = []
        if not s.target_platforms:
            s1 = StrategySuggestion("targeting", "high")
            s1.field = "target_platforms"
            s1.suggested_value = "Add target platforms"
            s1.reason = "No target platforms defined"
            s1.estimated_impact = "high"
            suggestions.append(s1)
        if not s.target_audience:
            s2 = StrategySuggestion("targeting", "medium")
            s2.field = "target_audience"
            s2.suggested_value = "Define target audience"
            s2.reason = "Audience targeting improves content relevance"
            suggestions.append(s2)
        return suggestions

    def _suggest_frequency(self, s: StrategyProfile) -> List[StrategySuggestion]:
        suggestions = []
        if s.posting_frequency == "daily" and s.avg_engagement < 0.3 and s.usage_count > 5:
            s1 = StrategySuggestion("frequency", "medium")
            s1.field = "posting_frequency"
            s1.current_value = s.posting_frequency
            s1.suggested_value = "reduce to every_other_day"
            s1.reason = "Low engagement with daily posting suggests audience fatigue"
            suggestions.append(s1)
        if not s.optimal_hours:
            s2 = StrategySuggestion("frequency", "low")
            s2.field = "optimal_hours"
            s2.suggested_value = "Identify optimal posting hours"
            s2.reason = "Posting at peak hours improves reach"
            suggestions.append(s2)
        return suggestions

    def _suggest_content_pillars(self, s: StrategyProfile) -> List[StrategySuggestion]:
        suggestions = []
        if len(s.content_pillars) < 2:
            s1 = StrategySuggestion("content", "medium")
            s1.field = "content_pillars"
            s1.suggested_value = "Add at least 3 content pillars"
            s1.reason = "Multiple pillars provide content variety and reduce burnout"
            suggestions.append(s1)
        return suggestions

    def _suggest_engagement_tactics(self, s: StrategyProfile) -> List[StrategySuggestion]:
        suggestions = []
        if len(s.engagement_tactics) == 0:
            s1 = StrategySuggestion("engagement", "medium")
            s1.field = "engagement_tactics"
            s1.suggested_value = "Add engagement tactics (polls, questions, CTAs)"
            s1.reason = "Active engagement tactics boost algorithmic reach"
            suggestions.append(s1)
        return suggestions

    def _suggest_from_patterns(self, s: StrategyProfile, patterns: List[StrategyPattern]) -> List[StrategySuggestion]:
        suggestions = []
        for pat in patterns:
            if pat.pattern_type == "success" and pat.platform:
                if pat.platform not in s.target_platforms:
                    s1 = StrategySuggestion("pattern", "high")
                    s1.field = "target_platforms"
                    s1.suggested_value = f"Add {pat.platform} (high performer)"
                    s1.reason = pat.description
                    s1.estimated_impact = "high"
                    suggestions.append(s1)
            elif pat.pattern_type == "failure":
                s2 = StrategySuggestion("pattern", "high")
                s2.field = "strategy_type"
                s2.reason = pat.description
                s2.estimated_impact = "high"
                suggestions.append(s2)
        return suggestions

    def _compute_confidence(self, s: StrategyProfile, suggestions: List[StrategySuggestion]) -> float:
        if not suggestions:
            return 0.0
        critical = sum(1 for sg in suggestions if sg.priority == "critical")
        high = sum(1 for sg in suggestions if sg.priority == "high")
        base = 0.5 + critical * 0.1 + high * 0.05
        if s.usage_count > 10:
            base += 0.1
        return round(min(1.0, base), 3)

    def get_results(self) -> List[StrategyOptimizationResult]:
        return list(self._results)

    @property
    def optimization_count(self) -> int:
        return len(self._results)
