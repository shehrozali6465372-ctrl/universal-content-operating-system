"""EvalRanker — rank evaluation results."""
from __future__ import annotations
from typing import Any, Dict, List
from .models import EvalResult

class EvalRanker:
    def rank(self, results: List[EvalResult]) -> List[Dict[str, Any]]:
        ranked = [{"type": r.eval_type.value, "score": r.score, "passed": r.passed} for r in results]
        ranked.sort(key=lambda x: x["score"], reverse=True)
        for i, r in enumerate(ranked): r["rank"] = i + 1
        return ranked
