"""Strategy Evaluator — Evaluate strategy quality and expected outcomes."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class EvaluationResult:
    """Result of strategy evaluation."""
    __slots__ = ("strategy_id", "overall_score", "dimensions", "strengths",
                 "weaknesses", "expected_outcomes", "grade")

    def __init__(self, strategy_id: str = "") -> None:
        self.strategy_id = strategy_id
        self.overall_score = 0.0
        self.dimensions: Dict[str, float] = {}
        self.strengths: List[str] = []
        self.weaknesses: List[str] = []
        self.expected_outcomes: Dict[str, Any] = {}
        self.grade = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "overall_score": round(self.overall_score, 3),
            "dimensions": {k: round(v, 3) for k, v in self.dimensions.items()},
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "expected_outcomes": self.expected_outcomes,
            "grade": self.grade,
        }


class StrategyEvaluator:
    """Evaluates strategies across multiple dimensions."""

    GRADE_THRESHOLDS = [
        (0.9, "A+"), (0.8, "A"), (0.7, "B+"), (0.6, "B"), (0.5, "C+"), (0.4, "C"), (0.0, "D"),
    ]
    WEIGHTS = {
        "feasibility": 0.2,
        "impact": 0.25,
        "confidence": 0.2,
        "risk_adjustment": 0.15,
        "resource_efficiency": 0.1,
        "alignment": 0.1,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = weights or self.WEIGHTS.copy()
        total = sum(self._weights.values())
        if total > 0:
            self._weights = {k: v / total for k, v in self._weights.items()}

    def evaluate(self, strategy_data: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a strategy and return scored result."""
        result = EvaluationResult(strategy_id=strategy_data.get("strategy_id", ""))

        # Score each dimension
        result.dimensions["feasibility"] = self._score_feasibility(strategy_data)
        result.dimensions["impact"] = self._score_impact(strategy_data)
        result.dimensions["confidence"] = strategy_data.get("confidence", 0.5)
        result.dimensions["risk_adjustment"] = self._score_risk_adjustment(strategy_data)
        result.dimensions["resource_efficiency"] = self._score_resource_efficiency(strategy_data)
        result.dimensions["alignment"] = self._score_alignment(strategy_data)

        # Overall
        result.overall_score = sum(
            result.dimensions.get(d, 0) * w for d, w in self._weights.items()
        )
        result.grade = self._assign_grade(result.overall_score)

        # Strengths / weaknesses
        result.strengths = self._identify_strengths(result.dimensions)
        result.weaknesses = self._identify_weaknesses(result.dimensions)

        # Expected outcomes
        result.expected_outcomes = self._predict_outcomes(strategy_data, result)

        return result

    def evaluate_batch(self, strategies: List[Dict[str, Any]]) -> List[EvaluationResult]:
        """Evaluate multiple strategies."""
        return [self.evaluate(s) for s in strategies]

    def compare(self, eval1: EvaluationResult, eval2: EvaluationResult) -> Dict[str, Any]:
        """Compare two evaluations."""
        diff = {}
        for dim in set(eval1.dimensions) | set(eval2.dimensions):
            diff[dim] = round(eval1.dimensions.get(dim, 0) - eval2.dimensions.get(dim, 0), 3)
        winner = eval1 if eval1.overall_score >= eval2.overall_score else eval2
        return {
            "winner": winner.strategy_id,
            "margin": round(abs(eval1.overall_score - eval2.overall_score), 3),
            "dimension_diff": diff,
        }

    def _score_feasibility(self, data: Dict[str, Any]) -> float:
        tactics = data.get("tactics", [])
        if not tactics:
            return 0.3
        effort_map = {"low": 0.9, "medium": 0.6, "high": 0.3}
        avg_effort = 0.5
        efforts = [t.get("effort", "medium") for t in tactics]
        scores = [effort_map.get(e, 0.5) for e in efforts]
        if scores:
            avg_effort = sum(scores) / len(scores)
        return avg_effort

    def _score_impact(self, data: Dict[str, Any]) -> float:
        score = data.get("score", 50) / 100.0
        confidence = data.get("confidence", 0.5)
        return round((score + confidence) / 2.0, 3)

    def _score_risk_adjustment(self, data: Dict[str, Any]) -> float:
        risk = data.get("risk_level", "medium")
        risk_map = {"low": 0.9, "medium": 0.6, "high": 0.3}
        return risk_map.get(risk, 0.5)

    def _score_resource_efficiency(self, data: Dict[str, Any]) -> float:
        tactics = data.get("tactics", [])
        if not tactics:
            return 0.5
        high_priority = sum(1 for t in tactics if t.get("priority", "") in ("HIGH", "CRITICAL"))
        return round(1.0 - (high_priority / max(len(tactics), 1)) * 0.3, 3)

    def _score_alignment(self, data: Dict[str, Any]) -> float:
        goals = data.get("goals", [])
        tactics = data.get("tactics", [])
        if not goals:
            return 0.3
        if len(goals) > 0 and len(tactics) > 0:
            return 0.8
        return 0.5

    def _assign_grade(self, score: float) -> str:
        for threshold, grade in self.GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "D"

    def _identify_strengths(self, dims: Dict[str, float]) -> List[str]:
        strengths: List[str] = []
        if dims.get("feasibility", 0) > 0.7:
            strengths.append("High feasibility — low effort tactics")
        if dims.get("impact", 0) > 0.7:
            strengths.append("High expected impact")
        if dims.get("confidence", 0) > 0.8:
            strengths.append("Strong confidence backing")
        if dims.get("risk_adjustment", 0) > 0.7:
            strengths.append("Low risk profile")
        return strengths

    def _identify_weaknesses(self, dims: Dict[str, float]) -> List[str]:
        weaknesses: List[str] = []
        if dims.get("feasibility", 1) < 0.4:
            weaknesses.append("Low feasibility — high effort required")
        if dims.get("impact", 1) < 0.4:
            weaknesses.append("Low expected impact")
        if dims.get("confidence", 1) < 0.4:
            weaknesses.append("Low confidence — uncertain outcome")
        if dims.get("risk_adjustment", 1) < 0.4:
            weaknesses.append("High risk")
        return weaknesses

    def _predict_outcomes(self, data: Dict[str, Any], eval_result: EvaluationResult) -> Dict[str, Any]:
        score = eval_result.overall_score
        return {
            "estimated_engagement": round(score * 0.01, 3),
            "probability_of_success": round(score / 100.0, 3),
            "expected_reach_multiplier": round(1.0 + (score / 200.0), 3),
            "recommended_action": "publish" if score > 60 else "revise" if score > 40 else "skip",
        }
