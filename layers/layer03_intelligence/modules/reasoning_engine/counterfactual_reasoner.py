"""Counterfactual Reasoner - What-if analysis for decisions."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class CounterfactualScenario:
    """A what-if scenario."""
    __slots__ = ("name", "original_value", "counterfactual_value",
                 "variable", "estimated_impact", "confidence", "reasoning")

    def __init__(self, name: str = "", variable: str = "",
                 original_value: Any = None, counterfactual_value: Any = None):
        self.name = name
        self.variable = variable
        self.original_value = original_value
        self.counterfactual_value = counterfactual_value
        self.estimated_impact = 0.0
        self.confidence = 0.0
        self.reasoning = ""

    def to_dict(self) -> Dict:
        return {
            "name": self.name, "variable": self.variable,
            "original": str(self.original_value),
            "counterfactual": str(self.counterfactual_value),
            "estimated_impact": round(self.estimated_impact, 3),
            "confidence": round(self.confidence, 3),
            "reasoning": self.reasoning,
        }


class CounterfactualResult:
    """Result of counterfactual analysis."""
    __slots__ = ("scenarios", "best_alternative", "overall_impact",
                 "recommendation", "reasoning")

    def __init__(self) -> None:
        self.scenarios: List[CounterfactualScenario] = []
        self.best_alternative: Optional[CounterfactualScenario] = None
        self.overall_impact = 0.0
        self.recommendation = ""
        self.reasoning: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "scenarios": [s.to_dict() for s in self.scenarios],
            "best_alternative": self.best_alternative.to_dict() if self.best_alternative else None,
            "overall_impact": round(self.overall_impact, 3),
            "recommendation": self.recommendation,
            "reasoning": list(self.reasoning),
        }


class CounterfactualReasoner:
    """Generates and evaluates what-if scenarios."""

    def __init__(self) -> None:
        self._templates: List[Dict] = []

    def add_template(self, variable: str, values: List[Any],
                     impact_fn: Optional[Any] = None) -> None:
        self._templates.append({"variable": variable, "values": values, "impact_fn": impact_fn})

    def analyze(self, original_context: Dict, original_score: float,
                templates: Optional[List[Dict]] = None) -> CounterfactualResult:
        result = CounterfactualResult()
        templates = templates or self._templates

        for template in templates:
            variable = template.get("variable", "")
            values = template.get("values", [])
            original_val = original_context.get(variable)

            for alt_value in values:
                if alt_value == original_val:
                    continue
                scenario = CounterfactualScenario(
                    name=f"if_{variable}_was_{alt_value}",
                    variable=variable,
                    original_value=original_val,
                    counterfactual_value=alt_value,
                )

                # Estimate impact
                modified_ctx = dict(original_context)
                modified_ctx[variable] = alt_value
                impact_fn = template.get("impact_fn")
                if callable(impact_fn):
                    new_score = impact_fn(modified_ctx)
                    scenario.estimated_impact = new_score - original_score
                    scenario.confidence = 0.7
                else:
                    # Simple heuristic: if changing a numeric variable
                    if isinstance(original_val, (int, float)) and isinstance(alt_value, (int, float)):
                        delta = alt_value - original_val
                        scenario.estimated_impact = delta * 0.1
                        scenario.confidence = 0.4
                    else:
                        scenario.estimated_impact = 0.0
                        scenario.confidence = 0.2

                scenario.reasoning = (
                    f"Changing {variable} from {original_val} to {alt_value} "
                    f"would impact score by {scenario.estimated_impact:+.3f}"
                )
                result.scenarios.append(scenario)

        # Find best alternative
        if result.scenarios:
            result.best_alternative = max(result.scenarios, key=lambda s: s.estimated_impact)
            result.overall_impact = result.best_alternative.estimated_impact

            if result.overall_impact > 0.05:
                result.recommendation = (
                    f"Consider changing {result.best_alternative.variable} "
                    f"to {result.best_alternative.counterfactual_value} "
                    f"(potential improvement: {result.overall_impact:+.3f})"
                )
                result.reasoning.append(f"Best alternative: {result.best_alternative.name}")
            else:
                result.recommendation = "Current decision appears near-optimal"

        return result
