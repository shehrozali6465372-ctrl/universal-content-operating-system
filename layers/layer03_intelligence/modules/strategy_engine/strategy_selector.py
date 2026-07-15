"""Strategy Selector — Select best strategy from alternatives."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class SelectionResult:
    """Result of strategy selection."""
    __slots__ = ("selected_id", "alternatives", "ranking", "reasoning", "confidence")

    def __init__(self) -> None:
        self.selected_id = ""
        self.alternatives: List[Dict[str, Any]] = []
        self.ranking: List[Dict[str, Any]] = []
        self.reasoning: List[str] = []
        self.confidence = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected": self.selected_id,
            "alternatives_count": len(self.alternatives),
            "ranking": self.ranking,
            "reasoning": self.reasoning,
            "confidence": round(self.confidence, 3),
        }


class StrategySelector:
    """Selects the best strategy from multiple candidates."""

    CRITERIA_WEIGHTS = {
        "score": 0.30,
        "confidence": 0.25,
        "feasibility": 0.20,
        "risk": 0.15,
        "novelty": 0.10,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = weights or self.CRITERIA_WEIGHTS.copy()

    def select(
        self, candidates: List[Dict[str, Any]], constraints: Optional[Dict[str, Any]] = None
    ) -> SelectionResult:
        """Select the best strategy from candidates."""
        result = SelectionResult()
        if not candidates:
            return result

        constraints = constraints or {}

        # Score each candidate
        scored: List[Dict[str, Any]] = []
        for c in candidates:
            s = self._score_candidate(c, constraints)
            scored.append({"candidate": c, "composite_score": s})

        # Sort by score descending
        scored.sort(key=lambda x: x["composite_score"], reverse=True)

        # Ranking
        for i, s in enumerate(scored):
            result.ranking.append({
                "rank": i + 1,
                "strategy_id": s["candidate"].get("strategy_id", s["candidate"].get("name", f"c{i}")),
                "score": round(s["composite_score"], 3),
            })

        best = scored[0]
        result.selected_id = best["candidate"].get("strategy_id", best["candidate"].get("name", ""))
        result.alternatives = [s["candidate"] for s in scored[1:]]
        result.confidence = best["composite_score"]
        result.reasoning = self._build_reasoning(scored, constraints)

        return result

    def _score_candidate(self, candidate: Dict[str, Any], constraints: Dict[str, Any]) -> float:
        s = 0.0
        s += self._weights.get("score", 0.3) * candidate.get("score", 50) / 100.0
        s += self._weights.get("confidence", 0.25) * candidate.get("confidence", 0.5)
        s += self._weights.get("feasibility", 0.2) * self._feasibility_score(candidate)
        risk = candidate.get("risk_score", 50) / 100.0
        s += self._weights.get("risk", 0.15) * (1.0 - risk)
        s += self._weights.get("novelty", 0.1) * candidate.get("novelty", 0.5)

        # Penalty for constraint violations
        min_score = constraints.get("min_score", 0)
        if candidate.get("score", 0) < min_score:
            s *= 0.5
        max_risk = constraints.get("max_risk", 1.0)
        if risk > max_risk:
            s *= 0.7

        return round(s, 4)

    def _feasibility_score(self, candidate: Dict[str, Any]) -> float:
        tactics = candidate.get("tactics", [])
        if not tactics:
            return 0.5
        effort_map = {"low": 0.9, "medium": 0.6, "high": 0.3}
        scores = [effort_map.get(t.get("effort", "medium"), 0.5) for t in tactics]
        return sum(scores) / len(scores) if scores else 0.5

    def _build_reasoning(self, scored: List[Dict], constraints: Dict) -> List[str]:
        reasons: List[str] = []
        if len(scored) >= 2:
            diff = scored[0]["composite_score"] - scored[1]["composite_score"]
            reasons.append(f"Selected strategy leads by {diff:.3f} over next best")
        reasons.append(f"Scored across {len(self._weights)} weighted criteria")
        if constraints:
            reasons.append(f"Applied {len(constraints)} constraint(s) during selection")
        return reasons
