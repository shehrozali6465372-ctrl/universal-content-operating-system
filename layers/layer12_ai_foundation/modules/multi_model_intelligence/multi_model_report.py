"""MultiModelReport — generate reports for multi-model intelligence."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class MultiModelReportGenerator:
    """Generate reports for multi-model intelligence operations."""

    def __init__(self) -> None:
        self._reports: List[Dict[str, Any]] = []

    def generate(self, metrics: Dict[str, Any], history: List[Dict[str, Any]],
                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        report = {
            "report_type": "multi_model_intelligence",
            "generated_at": time.time(),
            "metrics": metrics,
            "total_operations": len(history),
            "metadata": metadata or {},
        }

        if history:
            consensus_scores = [h.get("consensus_score", 0) for h in history]
            report["avg_consensus"] = sum(consensus_scores) / len(consensus_scores)
            report["best_consensus"] = max(consensus_scores) if consensus_scores else 0

        recommendations = []
        if metrics.get("success_rate", 1.0) < 0.8:
            recommendations.append("Consider adding fallback models")
        if metrics.get("avg_latency_ms", 0) > 5000:
            recommendations.append("Latency is high — consider faster models")
        if metrics.get("avg_consensus", 1.0) < 0.5:
            recommendations.append("Low consensus — models may need better prompts")
        report["recommendations"] = recommendations

        self._reports.append(report)
        return report

    def get_reports(self) -> List[Dict[str, Any]]:
        return list(self._reports)

    def export_json(self, report: Dict[str, Any]) -> str:
        import json
        return json.dumps(report, indent=2, default=str)
