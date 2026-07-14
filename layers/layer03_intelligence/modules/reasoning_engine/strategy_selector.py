"""Strategy Selector — picks best content strategy based on context."""

from typing import Dict, List, Optional


STRATEGIES = {
    "viral_hooks": {"engagement": 0.9, "reach": 0.8, "quality": 0.5},
    "educational": {"engagement": 0.6, "reach": 0.5, "quality": 0.9},
    "controversial": {"engagement": 0.8, "reach": 0.9, "quality": 0.3},
    "inspirational": {"engagement": 0.7, "reach": 0.6, "quality": 0.7},
    "data_driven": {"engagement": 0.5, "reach": 0.4, "quality": 0.95},
    "storytelling": {"engagement": 0.85, "reach": 0.7, "quality": 0.8},
}


class StrategyResult:
    def __init__(self, name: str, score: float = 0.0, factors: Optional[Dict] = None):
        self.name = name
        self.score = score
        self.factors = factors or {}
    def to_dict(self) -> dict:
        return {"name": self.name, "score": self.score, "factors": dict(self.factors)}


class StrategySelector:
    def __init__(self, niche_weights: Optional[Dict[str, float]] = None):
        self._strategies = dict(STRATEGIES)
        self._weights = niche_weights or {"engagement": 0.4, "reach": 0.3, "quality": 0.3}

    def select(self, context: Optional[Dict] = None) -> StrategyResult:
        best_name, best_score = "educational", 0.0
        for name, factors in self._strategies.items():
            score = sum(factors.get(f, 0) * w for f, w in self._weights.items())
            if score > best_score:
                best_score = score
                best_name = name
        return StrategyResult(best_name, round(best_score, 3), self._strategies[best_name])

    def select_top_n(self, n: int = 3) -> List[StrategyResult]:
        results = []
        for name, factors in self._strategies.items():
            score = sum(factors.get(f, 0) * w for f, w in self._weights.items())
            results.append(StrategyResult(name, round(score, 3), factors))
        return sorted(results, key=lambda r: -r.score)[:n]

    def add_strategy(self, name: str, factors: Dict[str, float]):
        self._strategies[name] = factors
