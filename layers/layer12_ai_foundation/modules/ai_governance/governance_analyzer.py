"""GovernanceAnalyzer — analyze governance patterns and compliance trends."""
from __future__ import annotations
from typing import Any, Dict, List

class GovernanceAnalyzer:
    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []
    def analyze(self, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not checks: return {"total": 0, "pass_rate": 0.0}
        passed = sum(1 for c in checks if c.get("passed", True))
        type_stats: Dict[str, Dict[str, int]] = {}
        for c in checks:
            t = c.get("type", "unknown")
            if t not in type_stats: type_stats[t] = {"total": 0, "passed": 0}
            type_stats[t]["total"] += 1
            if c.get("passed", True): type_stats[t]["passed"] += 1
        result = {"total": len(checks), "passed": passed,
                  "pass_rate": round(passed / len(checks), 4), "by_type": type_stats}
        self._history.append(result)
        return result
    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
