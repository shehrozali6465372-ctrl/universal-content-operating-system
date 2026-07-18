"""recovery_report.py — Recovery reporting."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class RecoveryReport:
    """Generates recovery reports."""

    def __init__(self) -> None:
        self._reports: List[Dict[str, Any]] = []

    def generate(self, metrics: Dict[str, Any], dr_plans: int = 0) -> Dict[str, Any]:
        report = {"metrics": metrics, "dr_plans": dr_plans,
                  "generated_at": time.time()}
        self._reports.append(report)
        return report

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._reports[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        return {"reports": len(self._reports)}
