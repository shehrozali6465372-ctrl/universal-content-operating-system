"""GovernanceMetrics — track governance performance."""
from __future__ import annotations
from typing import Any, Dict

class GovernanceMetrics:
    def __init__(self) -> None:
        self.total_checks: int = 0; self.total_passed: int = 0
        self.total_violations: int = 0; self.by_type: Dict[str, int] = {}
    def record(self, passed: bool, violation_type: str = "") -> None:
        self.total_checks += 1
        if passed: self.total_passed += 1
        else:
            self.total_violations += 1
            if violation_type: self.by_type[violation_type] = self.by_type.get(violation_type, 0) + 1
    @property
    def compliance_rate(self) -> float: return self.total_passed / max(self.total_checks, 1)
    def reset(self) -> None: self.__init__()
    def to_dict(self) -> Dict[str, Any]:
        return {"total_checks": self.total_checks, "compliance_rate": round(self.compliance_rate, 4),
                "total_violations": self.total_violations, "by_type": self.by_type}
