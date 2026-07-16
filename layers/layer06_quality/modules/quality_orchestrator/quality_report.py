"""Quality Report — Final unified report for Layer 7 consumption."""
from __future__ import annotations
from typing import Any, Dict, List


class ModuleExecutionRecord:
    """Record of a single module's execution."""

    __slots__ = ("module_name", "status", "duration_ms", "score",
                 "confidence", "issues_count", "error_message")

    def __init__(self, module_name: str = "") -> None:
        self.module_name = module_name
        self.status = "pending"  # pending, running, completed, failed, skipped
        self.duration_ms = 0.0
        self.score = 0.0
        self.confidence = 0.0
        self.issues_count = 0
        self.error_message = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 2),
            "score": round(self.score, 1),
            "confidence": round(self.confidence, 3),
            "issues_count": self.issues_count,
            "error_message": self.error_message,
        }


class QualityReport:
    """Final unified quality report consumed by Layer 7 (Publishing)."""

    __slots__ = (
        "report_id", "content_id", "overall_score", "confidence",
        "grade", "decision", "risk_level", "publish_readiness",
        "module_records", "explanations", "hard_stops",
        "total_duration_ms", "events", "metadata",
    )

    def __init__(self, report_id: str = "", content_id: str = "") -> None:
        self.report_id = report_id
        self.content_id = content_id
        self.overall_score = 0.0
        self.confidence = 0.0
        self.grade = "F"
        self.decision = "reject"
        self.risk_level = "critical"
        self.publish_readiness = 0.0
        self.module_records: List[ModuleExecutionRecord] = []
        self.explanations: List[Dict[str, Any]] = []
        self.hard_stops: List[str] = []
        self.total_duration_ms = 0.0
        self.events: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    def is_publishable(self) -> bool:
        """Check if content is ready to publish."""
        return self.decision in ("approve", "approve_with_warnings")

    def get_publish_readiness_label(self) -> str:
        if self.publish_readiness >= 0.9:
            return "Very High"
        if self.publish_readiness >= 0.75:
            return "High"
        if self.publish_readiness >= 0.5:
            return "Moderate"
        if self.publish_readiness >= 0.3:
            return "Low"
        return "Very Low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "content_id": self.content_id,
            "overall_score": round(self.overall_score, 1),
            "confidence": round(self.confidence, 3),
            "grade": self.grade,
            "decision": self.decision,
            "risk_level": self.risk_level,
            "publish_readiness": round(self.publish_readiness, 3),
            "publish_readiness_label": self.get_publish_readiness_label(),
            "is_publishable": self.is_publishable(),
            "module_records": [r.to_dict() for r in self.module_records],
            "explanations": self.explanations,
            "hard_stops": self.hard_stops,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "events": self.events,
            "metadata": self.metadata,
        }
