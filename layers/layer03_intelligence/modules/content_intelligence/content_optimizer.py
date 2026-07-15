"""Content Optimizer - Suggests content improvements."""
from __future__ import annotations
from typing import Dict, List


class OptimizationSuggestion:
    __slots__ = ("category", "issue", "suggestion", "priority", "impact")

    def __init__(self, category: str = "", issue: str = "", suggestion: str = "",
                 priority: str = "medium", impact: float = 0.5):
        self.category = category
        self.issue = issue
        self.suggestion = suggestion
        self.priority = priority
        self.impact = impact

    def to_dict(self) -> Dict:
        return {"category": self.category, "issue": self.issue,
                "suggestion": self.suggestion, "priority": self.priority,
                "impact": round(self.impact, 3)}


class OptimizationResult:
    __slots__ = ("suggestions", "optimized_score", "original_score", "improvement")

    def __init__(self) -> None:
        self.suggestions: List[OptimizationSuggestion] = []
        self.optimized_score = 0.0
        self.original_score = 0.0
        self.improvement = 0.0

    def to_dict(self) -> Dict:
        return {"suggestions": [s.to_dict() for s in self.suggestions],
                "original_score": round(self.original_score, 3),
                "optimized_score": round(self.optimized_score, 3),
                "improvement": round(self.improvement, 3)}


class ContentOptimizer:
    def optimize(self, content: str, scores: Dict[str, float]) -> OptimizationResult:
        result = OptimizationResult()
        result.original_score = sum(scores.values()) / max(len(scores), 1)

        suggestions = []
        if scores.get("quality", 1) < 0.7:
            suggestions.append(OptimizationSuggestion("quality", "Low quality score", "Improve grammar and clarity", "high", 0.3))
        if scores.get("readability", 1) < 0.6:
            suggestions.append(OptimizationSuggestion("readability", "Hard to read", "Shorten sentences and use simpler words", "high", 0.25))
        if scores.get("engagement", 1) < 0.5:
            suggestions.append(OptimizationSuggestion("engagement", "Low engagement potential", "Add questions, lists, or emotional hooks", "medium", 0.2))
        if scores.get("novelty", 1) < 0.5:
            suggestions.append(OptimizationSuggestion("novelty", "Content not unique", "Add unique angle or original data", "medium", 0.15))
        if scores.get("hook", 1) < 0.5:
            suggestions.append(OptimizationSuggestion("hook", "Weak opening", "Start with a compelling question or statistic", "high", 0.2))
        if scores.get("cta", 1) < 0.3:
            suggestions.append(OptimizationSuggestion("cta", "No call-to-action", "Add engagement prompt at the end", "low", 0.1))

        result.suggestions = sorted(suggestions, key=lambda s: {"high": 0, "medium": 1, "low": 2}.get(s.priority, 1))
        result.optimized_score = result.original_score + sum(s.impact for s in result.suggestions) * 0.3
        result.optimized_score = min(1.0, result.optimized_score)
        result.improvement = result.optimized_score - result.original_score
        return result
