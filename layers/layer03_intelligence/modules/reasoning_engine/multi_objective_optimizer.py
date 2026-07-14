"""Multi-objective Optimizer - Finds optimal solutions across competing objectives."""
from __future__ import annotations
from typing import Dict, List, Optional


class Objective:
    """A single optimization objective."""
    __slots__ = ("name", "weight", "direction", "target_value", "min_value")

    def __init__(self, name: str = "", weight: float = 1.0,
                 direction: str = "maximize", target_value: float = 1.0,
                 min_value: float = 0.0):
        self.name = name
        self.weight = weight
        self.direction = direction  # maximize or minimize
        self.target_value = target_value
        self.min_value = min_value

    def to_dict(self) -> Dict:
        return {"name": self.name, "weight": round(self.weight, 3),
                "direction": self.direction, "target": self.target_value}


class ParetoSolution:
    """A solution on the Pareto front."""
    __slots__ = ("name", "scores", "pareto_rank", "dominated_by", "nondomination_score")

    def __init__(self, name: str = "", scores: Optional[Dict[str, float]] = None):
        self.name = name
        self.scores = scores or {}
        self.pareto_rank = 0
        self.dominated_by = 0
        self.nondomination_score = 0.0

    def to_dict(self) -> Dict:
        return {"name": self.name, "scores": {k: round(v, 3) for k, v in self.scores.items()},
                "pareto_rank": self.pareto_rank, "nondomination_score": round(self.nondomination_score, 3)}


class MultiObjectiveResult:
    """Result of multi-objective optimization."""
    __slots__ = ("pareto_front", "best_compromise", "objectives",
                 "recommendations", "tradeoff_summary")

    def __init__(self) -> None:
        self.pareto_front: List[ParetoSolution] = []
        self.best_compromise: Optional[ParetoSolution] = None
        self.objectives: List[Objective] = []
        self.recommendations: List[str] = []
        self.tradeoff_summary = ""

    def to_dict(self) -> Dict:
        return {
            "pareto_front": [s.to_dict() for s in self.pareto_front],
            "best_compromise": self.best_compromise.to_dict() if self.best_compromise else None,
            "objectives": [o.to_dict() for o in self.objectives],
            "recommendations": list(self.recommendations),
            "tradeoff_summary": self.tradeoff_summary,
        }


class MultiObjectiveOptimizer:
    """Finds Pareto-optimal solutions across multiple objectives."""

    def __init__(self) -> None:
        self._objectives: List[Objective] = []

    def add_objective(self, objective: Objective) -> None:
        self._objectives.append(objective)

    def optimize(self, candidates: Dict[str, Dict[str, float]]) -> MultiObjectiveResult:
        result = MultiObjectiveResult()
        result.objectives = list(self._objectives)

        if not candidates or not self._objectives:
            return result

        # Build solutions
        solutions = []
        for name, scores in candidates.items():
            sol = ParetoSolution(name, scores)
            solutions.append(sol)

        # Calculate Pareto ranks
        for sol in solutions:
            for other in solutions:
                if other.name == sol.name:
                    continue
                if self._dominates(other.scores, sol.scores):
                    sol.dominated_by += 1

        # Rank by domination count
        solutions.sort(key=lambda s: s.dominated_by)
        for i, sol in enumerate(solutions):
            sol.pareto_rank = i
            sol.nondomination_score = 1.0 - (sol.dominated_by / max(len(solutions) - 1, 1))

        # Pareto front (rank 0)
        result.pareto_front = [s for s in solutions if s.dominated_by == 0]

        # Best compromise: weighted Tchebycheff
        weights = {o.name: o.weight for o in self._objectives}
        total_w = sum(weights.values())
        if total_w > 0:
            weights = {k: v / total_w for k, v in weights.items()}

        best = None
        best_score = -1
        for sol in result.pareto_front:
            score = sum(sol.scores.get(o.name, 0) * weights.get(o.name, 0) for o in self._objectives)
            if score > best_score:
                best_score = score
                best = sol

        result.best_compromise = best

        # Recommendations
        if best:
            weakest = min(best.scores.items(), key=lambda x: x[1])
            result.recommendations.append(
                f"Best compromise: '{best.name}' - consider improving '{weakest[0]}' (score: {weakest[1]:.2f})"
            )
            if len(result.pareto_front) > 1:
                result.tradeoff_summary = (
                    f"{len(result.pareto_front)} Pareto-optimal solutions found. "
                    f"No single solution dominates all others."
                )
            else:
                result.tradeoff_summary = "Single dominant solution found."

        return result

    def _dominates(self, a: Dict[str, float], b: Dict[str, float]) -> bool:
        """Check if solution a dominates solution b."""
        at_least_one_better = False
        for obj in self._objectives:
            val_a = a.get(obj.name, 0)
            val_b = b.get(obj.name, 0)
            if obj.direction == "maximize":
                if val_a < val_b:
                    return False
                if val_a > val_b:
                    at_least_one_better = True
            else:
                if val_a > val_b:
                    return False
                if val_a < val_b:
                    at_least_one_better = True
        return at_least_one_better
