"""DecisionMatrix — Multi-factor scoring and risk/reward analysis."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List, Optional

_DM_COUNTER = itertools.count(1)


class DecisionOption:
    """A decision option with multi-factor scores."""

    __slots__ = ("option_id", "name", "scores", "weight", "total_score")

    def __init__(self, name: str = "") -> None:
        self.option_id: str = f"opt_{next(_DM_COUNTER)}"
        self.name = name
        self.scores: Dict[str, float] = {}
        self.weight: float = 1.0
        self.total_score: float = 0.0

    def set_score(self, factor: str, score: float) -> None:
        self.scores[factor] = max(0.0, min(1.0, score))

    def compute_total(self, factor_weights: Optional[Dict[str, float]] = None) -> float:
        if not self.scores:
            return 0.0
        if factor_weights:
            total = sum(self.scores.get(f, 0) * w for f, w in factor_weights.items())
            weight_sum = sum(factor_weights.values())
            self.total_score = round(total / max(0.001, weight_sum) * self.weight, 4)
        else:
            self.total_score = round(sum(self.scores.values()) / len(self.scores) * self.weight, 4)
        return self.total_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id, "name": self.name,
            "total_score": self.total_score, "scores": self.scores,
        }


class DecisionMatrix:
    """Multi-factor decision scoring with risk vs reward analysis."""

    DEFAULT_FACTORS = ("impact", "effort", "risk", "confidence", "cost", "time")

    def __init__(self) -> None:
        self._options: List[DecisionOption] = []
        self._factor_weights: Dict[str, float] = {f: 1.0 for f in self.DEFAULT_FACTORS}
        self._decisions: List[Dict[str, Any]] = []

    def add_option(self, name: str) -> DecisionOption:
        option = DecisionOption(name)
        self._options.append(option)
        return option

    def set_factor_weight(self, factor: str, weight: float) -> None:
        self._factor_weights[factor] = weight

    def evaluate(self) -> Optional[DecisionOption]:
        for option in self._options:
            option.compute_total(self._factor_weights)
        if not self._options:
            return None
        best = max(self._options, key=lambda o: o.total_score)
        self._decisions.append({"best": best.name, "score": best.total_score})
        return best

    def risk_reward_analysis(self, option: DecisionOption) -> Dict[str, Any]:
        risk = option.scores.get("risk", 0.5)
        impact = option.scores.get("impact", 0.5)
        reward = impact * (1 - risk)
        return {
            "risk": round(risk, 3), "reward": round(reward, 3),
            "ratio": round(reward / max(0.001, risk), 3),
        }

    def cost_benefit(self, option: DecisionOption) -> Dict[str, Any]:
        cost = option.scores.get("cost", 0.5)
        impact = option.scores.get("impact", 0.5)
        benefit = impact - cost
        return {"cost": round(cost, 3), "benefit": round(impact, 3),
                "net": round(benefit, 3)}

    def get_all_options(self) -> List[DecisionOption]:
        return list(self._options)

    def get_stats(self) -> Dict[str, Any]:
        return {"options": len(self._options), "decisions_made": len(self._decisions)}
