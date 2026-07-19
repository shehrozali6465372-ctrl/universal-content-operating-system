"""CostReport — generate spending reports."""
from __future__ import annotations
import time
import json
from typing import Any, Dict, List, Optional

class CostReportGenerator:
    def __init__(self) -> None:
        self._reports: List[Dict[str, Any]] = []
    def generate(self, stats: Dict[str, Any], breakdown: Dict[str, Any],
                 recommendations: Optional[List[str]] = None) -> Dict[str, Any]:
        report = {"report_type": "cost_optimizer", "generated_at": time.time(),
                  "stats": stats, "breakdown": breakdown,
                  "recommendations": recommendations or []}
        if stats.get("total_cost", 0) > 10:
            report["recommendations"].append("Consider switching to cheaper models")
        self._reports.append(report)
        return report
    def export_json(self, report: Dict[str, Any]) -> str:
        return json.dumps(report, indent=2, default=str)
    def get_reports(self) -> List[Dict[str, Any]]:
        return list(self._reports)
