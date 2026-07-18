"""provider_report.py — Provider reporting."""
from __future__ import annotations
from typing import Any, Dict, List


class ProviderReport:
    """Generates reports for provider usage and performance."""

    def __init__(self) -> None:
        self._reports: List[Dict[str, Any]] = []

    def generate(self, metrics: Dict[str, Any], health: Dict[str, Any],
                 costs: Dict[str, Any]) -> Dict[str, Any]:
        report = {"metrics": metrics, "health": health, "costs": costs,
                  "summary": self._build_summary(metrics, health, costs)}
        self._reports.append(report)
        return report

    def _build_summary(self, metrics: Dict[str, Any], health: Dict[str, Any],
                       costs: Dict[str, Any]) -> Dict[str, Any]:
        total_requests = sum(m.get("requests", 0) for m in metrics.values())
        total_errors = sum(m.get("errors", 0) for m in metrics.values())
        total_cost = costs.get("total", 0.0)
        healthy_count = sum(1 for h in health.values() if h.get("status") == "healthy")
        return {"total_requests": total_requests, "total_errors": total_errors,
                "success_rate": (total_requests - total_errors) / total_requests if total_requests else 0,
                "total_cost": total_cost, "healthy_providers": healthy_count}

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._reports)

    def to_dict(self) -> Dict[str, Any]:
        return {"reports_count": len(self._reports),
                "latest": self._reports[-1] if self._reports else {}}
