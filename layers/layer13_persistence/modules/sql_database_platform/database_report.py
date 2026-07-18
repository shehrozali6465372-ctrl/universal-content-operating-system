"""database_report.py — Database reporting."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class DatabaseReport:
    """Generates database reports."""

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
        return {"reports": len(self._reports)}
