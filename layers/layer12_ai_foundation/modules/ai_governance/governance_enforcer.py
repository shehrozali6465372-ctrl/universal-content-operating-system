"""GovernanceEnforcer — fail-closed governance policy enforcement."""
from __future__ import annotations

from typing import Any, Dict, List


class GovernanceEnforcer:
    """Enforce governance results without silently allowing critical violations."""

    def __init__(self, block_on_critical: bool = True) -> None:
        self.block_on_critical = block_on_critical
        self._blocked: List[str] = []

    def enforce(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        violations = [r for r in results if not r.get("passed", True)]
        critical = [v for v in violations if str(v.get("severity", "")).lower() == "critical"]
        should_block = bool(critical) if self.block_on_critical else False
        if should_block:
            self._blocked.extend(
                str(v.get("rule") or v.get("message") or "critical_violation")
                for v in critical
            )
        return {
            "allowed": not should_block,
            "violations": len(violations),
            "critical": len(critical),
            "should_block": should_block,
            "blocked_rules": list(self._blocked),
        }
