"""EvalReport — generate evaluation reports."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class EvalReportGenerator:
    def __init__(self) -> None:
        self._reports: List[Dict[str, Any]] = []
    def generate(self, metrics: Dict[str, Any], issues: List[str] | None = None) -> Dict[str, Any]:
        report = {"report_type": "ai_evaluation", "generated_at": time.time(),
                  "metrics": metrics, "issues": issues or [], "recommendations": []}
        if metrics.get("pass_rate", 1.0) < 0.7: report["recommendations"].append("Low pass rate — review quality")
        self._reports.append(report); return report
    def get_reports(self) -> List[Dict[str, Any]]:
        return list(self._reports)
