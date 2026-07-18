"""sql_report.py — SQL platform reporting."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class SQLReport:
    """Generates SQL platform reports."""

    def __init__(self) -> None:
        self._reports: List[Dict[str, Any]] = []

    def generate(self, metrics: Dict[str, Any], health: Dict[str, Any],
                 pool_stats: Dict[str, Any]) -> Dict[str, Any]:
        report = {"metrics": metrics, "health": health, "pool": pool_stats,
                  "generated_at": time.time()}
        self._reports.append(report)
        return report

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._reports[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        return {"reports_count": len(self._reports),
                "latest": self._reports[-1] if self._reports else {}}
