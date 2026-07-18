"""PromptSuggester — suggest prompt improvements based on analysis."""
from __future__ import annotations

from typing import List

from .prompt_analyzer import PromptAnalyzer


class PromptSuggester:
    """Suggest prompt improvements based on analysis."""

    def __init__(self) -> None:
        self.analyzer = PromptAnalyzer()

    def suggest(self, prompt: str) -> List[str]:
        analysis = self.analyzer.analyze(prompt)
        suggestions: List[str] = []

        if analysis["word_count"] < 5:
            suggestions.append("Prompt is too short — add more context and instructions")
        if analysis["word_count"] > 500:
            suggestions.append("Prompt is very long — consider breaking into smaller parts")
        if analysis["question_count"] > 3:
            suggestions.append("Too many questions — focus on one clear objective")
        if not analysis["has_instructions"]:
            suggestions.append("Add explicit instructions (e.g., 'Write a detailed analysis')")
        if analysis["complexity_score"] < 0.2:
            suggestions.append("Low complexity — consider adding specific constraints")
        if not analysis["has_variables"]:
            suggestions.append("Consider using variables {{variable}} for reusable templates")
        if analysis["vocabulary_richness"] < 0.3:
            suggestions.append("Low vocabulary diversity — add more specific terminology")

        return suggestions

    def suggest_role(self, task: str) -> str:
        task_lower = task.lower()
        if any(w in task_lower for w in ["write", "blog", "article", "story"]):
            return "writer"
        if any(w in task_lower for w in ["code", "program", "debug", "api"]):
            return "coder"
        if any(w in task_lower for w in ["analyze", "data", "report", "metrics"]):
            return "analyst"
        if any(w in task_lower for w in ["review", "critique", "feedback"]):
            return "critic"
        if any(w in task_lower for w in ["plan", "strategy", "roadmap"]):
            return "strategist"
        if any(w in task_lower for w in ["research", "investigate", "find"]):
            return "researcher"
        if any(w in task_lower for w in ["design", "creative", "ideate"]):
            return "creative"
        return "assistant"
