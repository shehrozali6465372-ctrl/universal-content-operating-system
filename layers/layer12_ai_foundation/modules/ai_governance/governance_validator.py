"""GovernanceValidator — validate governance inputs."""
from __future__ import annotations
from typing import Any, Dict, List
from .models import Policy

class GovernanceValidator:
    def validate_content(self, content: str) -> Dict[str, Any]:
        issues: List[str] = []
        if not content or not content.strip(): issues.append("Empty content")
        return {"valid": len(issues) == 0, "issues": issues}
    def validate_policy(self, policy: Policy) -> Dict[str, Any]:
        issues: List[str] = []
        if not policy.name: issues.append("Missing policy name")
        if not policy.rules: issues.append("No rules defined")
        return {"valid": len(issues) == 0, "issues": issues}
