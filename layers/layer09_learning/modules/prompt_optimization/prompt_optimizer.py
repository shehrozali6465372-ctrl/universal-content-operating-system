"""Prompt Optimizer — Generate optimized prompt suggestions."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.prompt_optimization.prompt_profile import PromptProfile
from layers.layer09_learning.modules.prompt_optimization.prompt_analyzer import AnalysisReport


class OptimizationSuggestion:
    """A single suggestion for prompt improvement."""

    __slots__ = ("suggestion_id", "suggestion_type", "priority",
                 "field", "current_value", "suggested_value",
                 "reason", "estimated_impact")

    _counter = 0

    def __init__(self, suggestion_type: str = "template", priority: str = "medium") -> None:
        PromptOptimizer._counter += 1
        self.suggestion_id: str = f"os_{PromptOptimizer._counter}"
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
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
            "reason": self.reason,
            "estimated_impact": self.estimated_impact,
        }


class OptimizationResult:
    """Result of optimizing a prompt."""

    __slots__ = ("profile_id", "suggestions", "optimized_template",
                 "confidence", "changes_made")

    def __init__(self, profile_id: str = "") -> None:
        self.profile_id = profile_id
        self.suggestions: List[OptimizationSuggestion] = []
        self.optimized_template: str = ""
        self.confidence: float = 0.0
        self.changes_made: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "suggestion_count": len(self.suggestions),
            "optimized_template": self.optimized_template,
            "confidence": round(self.confidence, 3),
            "changes_made": self.changes_made,
        }


class PromptOptimizer:
    """Generate optimization suggestions for prompts."""

    _counter = 0

    def __init__(self) -> None:
        self._results: List[OptimizationResult] = []

    def optimize(self, profile: PromptProfile, analysis: Optional[AnalysisReport] = None) -> OptimizationResult:
        result = OptimizationResult(profile.profile_id)
        suggestions = []
        suggestions.extend(self._suggest_template_improvements(profile))
        suggestions.extend(self._suggest_parameter_adjustments(profile))
        suggestions.extend(self._suggest_metadata_improvements(profile))
        if analysis:
            suggestions.extend(self._suggest_from_analysis(profile, analysis))
        result.suggestions = suggestions
        result.optimized_template = self._apply_suggestions(profile, suggestions)
        result.changes_made = len(suggestions)
        result.confidence = self._compute_optimization_confidence(profile, suggestions)
        self._results.append(result)
        return result

    def _suggest_template_improvements(self, p: PromptProfile) -> List[OptimizationSuggestion]:
        suggestions = []
        if not p.template:
            s = OptimizationSuggestion("template", "critical")
            s.field = "template"
            s.current_value = ""
            s.suggested_value = "Add a detailed prompt template"
            s.reason = "Empty template cannot produce quality output"
            s.estimated_impact = "high"
            suggestions.append(s)
        elif len(p.template) < 30 and p.avg_quality_score < 0.6:
            s = OptimizationSuggestion("template", "high")
            s.field = "template"
            s.current_value = p.template[:50]
            s.suggested_value = "Expand with more specific instructions"
            s.reason = "Short prompts with low quality need more detail"
            s.estimated_impact = "high"
            suggestions.append(s)
        return suggestions

    def _suggest_parameter_adjustments(self, p: PromptProfile) -> List[OptimizationSuggestion]:
        suggestions = []
        if not p.platform:
            s = OptimizationSuggestion("parameter", "medium")
            s.field = "platform"
            s.current_value = ""
            s.suggested_value = "Add target platform"
            s.reason = "Platform-specific prompts produce better results"
            suggestions.append(s)
        if not p.tone:
            s = OptimizationSuggestion("parameter", "medium")
            s.field = "tone"
            s.current_value = ""
            s.suggested_value = "Define target tone"
            s.reason = "Tone guidance helps LLM produce consistent output"
            suggestions.append(s)
        return suggestions

    def _suggest_metadata_improvements(self, p: PromptProfile) -> List[OptimizationSuggestion]:
        suggestions = []
        if not p.tags:
            s = OptimizationSuggestion("metadata", "low")
            s.field = "tags"
            s.suggested_value = "Add descriptive tags"
            s.reason = "Tags help organize and retrieve prompts"
            suggestions.append(s)
        return suggestions

    def _suggest_from_analysis(self, p: PromptProfile, analysis: AnalysisReport) -> List[OptimizationSuggestion]:
        suggestions = []
        for finding in analysis.findings:
            if finding.recommendation:
                s = OptimizationSuggestion("analysis", "medium")
                s.field = finding.metric_name
                s.reason = finding.recommendation
                s.suggested_value = finding.recommendation
                s.estimated_impact = "medium" if finding.severity == "warning" else "high"
                suggestions.append(s)
        return suggestions

    def _apply_suggestions(self, p: PromptProfile, suggestions: List[OptimizationSuggestion]) -> str:
        if not p.template and any(s.field == "template" for s in suggestions):
            return "[OPTIMIZED] " + (p.template or "New prompt template")
        return p.template

    def _compute_optimization_confidence(self, p: PromptProfile, suggestions: List[OptimizationSuggestion]) -> float:
        if not suggestions:
            return 0.0
        critical = sum(1 for s in suggestions if s.priority == "critical")
        high = sum(1 for s in suggestions if s.priority == "high")
        base = 0.5 + critical * 0.1 + high * 0.05
        if p.usage_count > 10:
            base += 0.1
        return round(min(1.0, base), 3)

    def get_results(self) -> List[OptimizationResult]:
        return list(self._results)

    @property
    def optimization_count(self) -> int:
        return len(self._results)
