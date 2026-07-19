"""ReasoningReport — generate reports for reasoning operations."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class ReasoningReportGenerator:
    """Generate reports for reasoning engine operations."""

    def __init__(self) -> None:
        self._reports: List[Dict[str, Any]] = []

    def generate(self, metrics: Dict[str, Any],
                 memory_stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        report = {"report_type": "reasoning_engine", "generated_at": time.time(),
                  "metrics": metrics, "memory": memory_stats or {},
                  "recommendations": []}
        if metrics.get("avg_confidence", 1.0) < 0.5:
            report["recommendations"].append("Low average confidence — review reasoning quality")
        if metrics.get("verification_rate", 1.0) < 0.5:
            report["recommendations"].append("Low verification rate — improve chain structure")
        self._reports.append(report)
        return report

    def get_reports(self) -> List[Dict[str, Any]]:
        return list(self._reports)
