"""MemoryReport — generate reports for memory system."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class MemoryReportGenerator:
    """Generate reports for the AI memory system."""

    def __init__(self) -> None:
        self._reports: List[Dict[str, Any]] = []

    def generate(self, metrics: Dict[str, Any], stats: Dict[str, Any],
                 health: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        report = {
            "report_type": "ai_memory",
            "generated_at": time.time(),
            "metrics": metrics,
            "stats": stats,
            "health": health or {},
            "recommendations": [],
        }
        if metrics.get("hit_rate", 1.0) < 0.5:
            report["recommendations"].append("Low cache hit rate — increase cache size")
        if metrics.get("total_evictions", 0) > 100:
            report["recommendations"].append("High eviction rate — increase memory capacity")
        self._reports.append(report)
        return report

    def get_reports(self) -> List[Dict[str, Any]]:
        return list(self._reports)
