"""GovernanceEnforcer — enforce governance policies."""
from __future__ import annotations
from typing import Any, Dict, List

class GovernanceEnforcer:
    def __init__(self, block_on_critical: bool = True) -> None:
        self.block_on_critical = block_on_critical; self._blocked: List[str] = []
    def enforce(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        violations = [r for r in results if not r.get("passed", True)]
        critical = [v for v in violations if v.get("severity") == "critical"]
        should_block = self.block_on_critical and len(critical) > 0
        return {"allowed": not should_block, "violations": len(violations),
                "critical": len(critical), "should_block": should_block}
