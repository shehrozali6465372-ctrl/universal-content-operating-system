"""Explainability Engine — Generate human-readable explanations for decisions."""
from __future__ import annotations
from typing import List

from layers.layer06_quality.modules.quality_scoring_engine.quality_result import ModuleScore, ExplanationItem


class ExplainabilityEngine:
    """Generate explanations for quality decisions."""

    def __init__(self) -> None:
        self._explain_count = 0

    def explain(
        self,
        overall_score: float,
        module_scores: List[ModuleScore],
        decision: str = "",
        risk_level: str = "",
    ) -> List[ExplanationItem]:
        """Generate explanation items from module scores."""
        explanations: List[ExplanationItem] = []

        for ms in module_scores:
            if ms.score >= 90:
                explanations.append(ExplanationItem(
                    icon="✓", text=f"{ms.module_name} excellent ({ms.score:.0f})",
                    category=ms.module_name, severity="positive",
                ))
            elif ms.score >= 70:
                explanations.append(ExplanationItem(
                    icon="✓", text=f"{ms.module_name} good ({ms.score:.0f})",
                    category=ms.module_name, severity="positive",
                ))
            elif ms.score >= 50:
                explanations.append(ExplanationItem(
                    icon="⚠", text=f"{ms.module_name} needs improvement ({ms.score:.0f})",
                    category=ms.module_name, severity="warning",
                ))
            else:
                explanations.append(ExplanationItem(
                    icon="✗", text=f"{ms.module_name} failing ({ms.score:.0f})",
                    category=ms.module_name, severity="critical",
                ))

            for issue in ms.critical_issues:
                explanations.append(ExplanationItem(
                    icon="✗", text=f"Critical: {issue}",
                    category=ms.module_name, severity="critical",
                ))

        if decision:
            explanations.append(ExplanationItem(
                icon="→", text=f"Decision: {decision.upper().replace('_', ' ')}",
                category="decision", severity="info",
            ))

        if risk_level:
            explanations.append(ExplanationItem(
                icon="⚠" if risk_level in ("high", "critical") else "ℹ",
                text=f"Risk Level: {risk_level.upper()}",
                category="risk", severity="info" if risk_level == "low" else "warning",
            ))

        self._explain_count += 1
        return explanations

    def format_summary(
        self,
        overall_score: float,
        grade: str,
        decision: str,
        explanations: List[ExplanationItem],
    ) -> str:
        """Format a human-readable summary."""
        lines = [f"Overall Quality: {overall_score:.1f} (Grade: {grade})"]
        lines.append(f"Decision: {decision.upper().replace('_', ' ')}")
        lines.append("")
        for exp in explanations:
            lines.append(f"  {exp.icon} {exp.text}")
        return "\n".join(lines)

    @property
    def explain_count(self) -> int:
        return self._explain_count
