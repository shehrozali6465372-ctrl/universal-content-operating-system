"""GenerationReport — Content generation reports."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_GR_COUNTER = itertools.count(1)


class GenerationReport:
    """A content generation report."""

    __slots__ = ("report_id", "total_content", "by_platform", "by_type",
                 "avg_quality", "recommendations", "timestamp")

    def __init__(self) -> None:
        self.report_id: str = f"grep_{next(_GR_COUNTER)}"
        self.total_content: int = 0
        self.by_platform: Dict[str, int] = {}
        self.by_type: Dict[str, int] = {}
        self.avg_quality: float = 0.0
        self.recommendations: List[str] = []
        self.timestamp: float = time.time()

    def set_summary(self, data: Dict[str, Any]) -> None:
        self.total_content = data.get("total_generated", 0)
        self.by_platform = data.get("by_platform", {})
        self.by_type = data.get("by_type", {})
        self.avg_quality = data.get("avg_quality", 0.0)

    def add_recommendation(self, rec: str) -> None:
        self.recommendations.append(rec)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id, "total_content": self.total_content,
            "avg_quality": round(self.avg_quality, 3),
            "recommendation_count": len(self.recommendations),
        }

    def export_dict(self) -> Dict[str, Any]:
        return {**self.get_summary(), "by_platform": self.by_platform,
                "by_type": self.by_type, "recommendations": self.recommendations}
