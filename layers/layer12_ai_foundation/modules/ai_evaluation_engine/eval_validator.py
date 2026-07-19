"""EvalValidator — validate evaluation inputs."""
from __future__ import annotations
from typing import Any, Dict, List

class EvalValidator:
    def validate_content(self, content: str) -> Dict[str, Any]:
        issues: List[str] = []
        if not content or not content.strip(): issues.append("Empty content")
        if len(content) > 50000: issues.append("Content too long")
        return {"valid": len(issues) == 0, "issues": issues}
    def validate_criteria(self, criteria: Dict[str, float]) -> Dict[str, Any]:
        issues: List[str] = []
        for name, weight in criteria.items():
            if weight < 0: issues.append(f"Negative weight for {name}")
            if weight > 10: issues.append(f"Excessive weight for {name}")
        return {"valid": len(issues) == 0, "issues": issues}
