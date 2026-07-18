"""persistence_report.py — Persistence reporting."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class PersistenceReport:
    """Generates reports for persistence system."""

    __slots__ = ("_reports",)

    def __init__(self) -> None:
        self._reports: List[Dict[str, Any]] = []

    def generate(self, metrics: Dict[str, Any], health: Dict[str, Any],
                 stores: Dict[str, Any]) -> Dict[str, Any]:
        report = {"metrics": metrics, "health": health, "stores": stores,
                  "summary": self._build_summary(metrics, health, stores),
                  "generated_at": time.time()}
        self._reports.append(report)
        return report

    def _build_summary(self, metrics: Dict[str, Any], health: Dict[str, Any],
                       stores: Dict[str, Any]) -> Dict[str, Any]:
        return {"total_stores": len(stores),
                "total_operations": metrics.get("total_operations", 0),
                "error_rate": metrics.get("error_rate", 0.0),
                "health_status": health.get("status", "unknown")}

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._reports[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        return {"reports_count": len(self._reports),
                "latest": self._reports[-1] if self._reports else {}}
