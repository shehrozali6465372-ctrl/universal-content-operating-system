"""EvalEnforcer — enforce evaluation quality standards."""
from __future__ import annotations
from typing import Any, Dict, List
from .models import EvalResult

class EvalEnforcer:
    def __init__(self, min_pass_rate: float = 0.7) -> None:
        self.min_pass_rate = min_pass_rate
    def enforce(self, results: List[EvalResult]) -> Dict[str, Any]:
        if not results: return {"passes": False, "reason": "no results"}
        pass_rate = sum(1 for r in results if r.passed) / len(results)
        return {"passes": pass_rate >= self.min_pass_rate, "pass_rate": pass_rate,
                "total": len(results), "passed": sum(1 for r in results if r.passed)}
