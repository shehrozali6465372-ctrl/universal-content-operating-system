"""EvalMetrics — track evaluation metrics."""
from __future__ import annotations
from typing import Any, Dict

class EvalMetrics:
    def __init__(self) -> None:
        self.total_evaluations: int = 0; self.total_passed: int = 0
        self.by_type: Dict[str, int] = {}; self.total_score: float = 0.0
    def record(self, eval_type: str, score: float, passed: bool) -> None:
        self.total_evaluations += 1
        if passed: self.total_passed += 1
        self.by_type[eval_type] = self.by_type.get(eval_type, 0) + 1
        self.total_score += score
    @property
    def avg_score(self) -> float: return self.total_score / max(self.total_evaluations, 1)
    @property
    def pass_rate(self) -> float: return self.total_passed / max(self.total_evaluations, 1)
    def reset(self) -> None: self.__init__()
    def to_dict(self) -> Dict[str, Any]:
        return {"total": self.total_evaluations, "passed": self.total_passed,
                "pass_rate": round(self.pass_rate, 4), "avg_score": round(self.avg_score, 4)}
