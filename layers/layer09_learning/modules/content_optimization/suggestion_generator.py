"""Suggestion Generator — Generate prioritized optimization suggestions."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_SG_COUNTER = itertools.count(1)


class OptimizationSuggestion:
    """A single optimization suggestion."""

    __slots__ = ("suggestion_id", "field", "priority", "description",
                 "current_value", "suggested_value", "expected_impact",
                 "source_rule", "confidence")

    def __init__(self, field: str = "", priority: str = "medium") -> None:
        self.suggestion_id: str = f"osg_{next(_SG_COUNTER)}"
        self.field = field
        self.priority = priority
        self.description: str = ""
        self.current_value: str = ""
        self.suggested_value: str = ""
        self.expected_impact: float = 0.5
        self.source_rule: str = ""
        self.confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "field": self.field,
            "priority": self.priority,
            "description": self.description,
            "suggested_value": self.suggested_value,
            "expected_impact": round(self.expected_impact, 3),
        }


class SuggestionGenerator:
    """Generate optimization suggestions from analysis and rules."""

    def __init__(self) -> None:
        self._suggestions: List[OptimizationSuggestion] = []

    def generate(self, content: str, analysis: Dict[str, Any],
                 goal: str = "engagement",
                 max_suggestions: int = 5) -> List[OptimizationSuggestion]:
        self._suggestions.clear()
        weaknesses = analysis.get("weaknesses", [])
        for w in weaknesses:
            s = self._from_weakness(w, goal)
            if s:
                self._suggestions.append(s)
        self._suggestions.extend(self._title_suggestions(content, analysis))
        self._suggestions.extend(self._cta_suggestions(content, analysis))
        self._suggestions.extend(self._seo_suggestions(content, analysis))
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self._suggestions.sort(key=lambda s: priority_order.get(s.priority, 4))
        return self._suggestions[:max_suggestions]

    def _from_weakness(self, weakness: str, goal: str) -> OptimizationSuggestion | None:
        mapping = {
            "readability": ("body", "medium", "Simplify language and shorten sentences"),
            "hook": ("opening", "high", "Add a compelling hook at the start"),
            "cta": ("cta", "high", "Add a clear call-to-action"),
            "short": ("body", "medium", "Expand content with more detail"),
            "engagement": ("body", "medium", "Add interactive elements (questions, polls)"),
        }
        for key, (field, priority, desc) in mapping.items():
            if key in weakness.lower():
                s = OptimizationSuggestion(field, priority)
                s.description = desc
                s.expected_impact = 0.7
                return s
        return None

    def _title_suggestions(self, content: str, analysis: Dict[str, Any]) -> List[OptimizationSuggestion]:
        suggestions = []
        first_line = content.split("\n")[0] if "\n" in content else ""
        if first_line and len(first_line) > 60:
            s = OptimizationSuggestion("title", "high")
            s.description = "Shorten opening line to under 60 characters"
            s.suggested_value = first_line[:57] + "..."
            s.expected_impact = 0.6
            suggestions.append(s)
        return suggestions

    def _cta_suggestions(self, content: str, analysis: Dict[str, Any]) -> List[OptimizationSuggestion]:
        suggestions = []
        cta_score = analysis.get("cta_strength", 0.5)
        if cta_score < 0.5:
            s = OptimizationSuggestion("cta", "high")
            s.description = "Add a clear call-to-action at the end"
            s.suggested_value = "Add CTA: 'What do you think? Share your thoughts below!'"
            s.expected_impact = 0.7
            suggestions.append(s)
        return suggestions

    def _seo_suggestions(self, content: str, analysis: Dict[str, Any]) -> List[OptimizationSuggestion]:
        suggestions = []
        seo_score = analysis.get("seo_score", 0.5)
        if seo_score < 0.5:
            s = OptimizationSuggestion("seo", "medium")
            s.description = "Add relevant hashtags and keywords"
            s.expected_impact = 0.5
            suggestions.append(s)
        return suggestions

    def get_suggestions(self) -> List[OptimizationSuggestion]:
        return list(self._suggestions)
