"""PromptOptimizer — optimize prompts for better AI output quality."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import OptimizedPrompt


class PromptOptimizer:
    """Optimize prompts for better AI output quality."""

    OPTIMIZATION_TECHNIQUES = [
        "clarity", "specificity", "context_enrichment",
        "constraint_addition", "role_assignment", "output_format",
        "step_by_step", "examples", "temperature_hint",
    ]

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def optimize(self, prompt: str, task_type: str = "general",
                 techniques: Optional[List[str]] = None) -> OptimizedPrompt:
        techniques = techniques or self.OPTIMIZATION_TECHNIQUES
        optimized = prompt
        applied: List[str] = []

        if "clarity" in techniques:
            optimized, ok = self._apply_clarity(optimized)
            if ok:
                applied.append("clarity")

        if "specificity" in techniques:
            optimized, ok = self._apply_specificity(optimized, task_type)
            if ok:
                applied.append("specificity")

        if "context_enrichment" in techniques:
            optimized, ok = self._apply_context(optimized, task_type)
            if ok:
                applied.append("context_enrichment")

        if "constraint_addition" in techniques:
            optimized, ok = self._apply_constraints(optimized, task_type)
            if ok:
                applied.append("constraint_addition")

        if "role_assignment" in techniques:
            optimized, ok = self._apply_role(optimized, task_type)
            if ok:
                applied.append("role_assignment")

        if "output_format" in techniques:
            optimized, ok = self._apply_format(optimized, task_type)
            if ok:
                applied.append("output_format")

        if "step_by_step" in techniques:
            optimized, ok = self._apply_steps(optimized)
            if ok:
                applied.append("step_by_step")

        score = len(applied) / len(techniques) if techniques else 0.0
        result = OptimizedPrompt(
            original=prompt, optimized=optimized,
            improvement_score=score, optimizations_applied=applied,
        )
        self._history.append(result.to_dict())
        return result

    @staticmethod
    def _apply_clarity(prompt: str) -> tuple:
        if len(prompt.split()) < 5:
            return prompt + ". Be clear and specific.", True
        return prompt, False

    @staticmethod
    def _apply_specificity(prompt: str, task_type: str) -> tuple:
        if "briefly" not in prompt.lower() and "specifically" not in prompt.lower():
            if task_type == "writing":
                return prompt + " Write in a clear, engaging style.", True
            return prompt + " Be specific in your response.", True
        return prompt, False

    @staticmethod
    def _apply_context(prompt: str, task_type: str) -> tuple:
        if task_type and not any(f"[{task_type}]" in prompt for _ in [1]):
            return f"[Task: {task_type}] {prompt}", True
        return prompt, False

    @staticmethod
    def _apply_constraints(prompt: str, task_type: str) -> tuple:
        if "must not" not in prompt.lower() and "do not" not in prompt.lower():
            return prompt + " Ensure accuracy and relevance.", True
        return prompt, False

    @staticmethod
    def _apply_role(prompt: str, task_type: str) -> tuple:
        if "act as" not in prompt.lower() and "you are" not in prompt.lower():
            roles = {"writing": "skilled writer", "coding": "expert programmer",
                     "analysis": "data analyst", "creative": "creative director"}
            role = roles.get(task_type, "knowledgeable assistant")
            return f"You are a {role}. {prompt}", True
        return prompt, False

    @staticmethod
    def _apply_format(prompt: str, task_type: str) -> tuple:
        if "format" not in prompt.lower() and "json" not in prompt.lower():
            if task_type == "analysis":
                return prompt + " Provide structured output with clear sections.", True
            return prompt + " Format your response clearly.", True
        return prompt, False

    @staticmethod
    def _apply_steps(prompt: str) -> tuple:
        if "step" not in prompt.lower() and "chain" not in prompt.lower():
            return prompt + " Think step by step.", True
        return prompt, False

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
