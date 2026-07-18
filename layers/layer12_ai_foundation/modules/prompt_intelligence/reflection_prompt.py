"""ReflectionPrompt — generate self-reflection prompts for AI self-improvement."""
from __future__ import annotations

from typing import Any, Dict, List


class ReflectionPrompt:
    """Generate self-reflection prompts for AI self-improvement."""

    TEMPLATES: Dict[str, str] = {
        "quality_review": (
            "Review the following AI output for quality issues:\n"
            "Output: {output}\n\n"
            "Check for:\n1. Accuracy\n2. Clarity\n3. Completeness\n"
            "4. Relevance\n5. Grammar\n\nProvide improvement suggestions:"
        ),
        "mistake_analysis": (
            "Analyze this mistake:\n"
            "Task: {task}\nExpected: {expected}\nActual: {actual}\n\n"
            "What went wrong and how to prevent it next time:"
        ),
        "strategy_review": (
            "Review this strategy's effectiveness:\n"
            "Strategy: {strategy}\nResults: {results}\n\n"
            "Should we continue, modify, or abandon this strategy:"
        ),
        "output_improvement": (
            "Improve this output:\n{output}\n\n"
            "Requirements: {requirements}\n"
            "Better version:"
        ),
    }

    def __init__(self) -> None:
        self._custom: Dict[str, str] = {}

    def generate(self, template_name: str, **kwargs: Any) -> str:
        template = self._custom.get(template_name, self.TEMPLATES.get(template_name, ""))
        if not template:
            return f"No template found: {template_name}"
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def register(self, name: str, template: str) -> None:
        self._custom[name] = template

    def list_templates(self) -> List[str]:
        return list(set(list(self.TEMPLATES.keys()) + list(self._custom.keys())))

    def to_dict(self) -> Dict[str, str]:
        all_templates = dict(self.TEMPLATES)
        all_templates.update(self._custom)
        return all_templates
