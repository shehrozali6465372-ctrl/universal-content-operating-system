"""Workflow Report — Generate workflow execution reports."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_WR_COUNTER = itertools.count(1)


class WorkflowReport:
    """Report from a completed workflow execution."""

    __slots__ = ("report_id", "workflow_id", "name", "stages_executed",
                 "stages_failed", "total_duration_ms", "success",
                 "warnings", "recommendations", "stage_details", "timestamp")

    def __init__(self, workflow_id: str = "", name: str = "") -> None:
        self.report_id: str = f"wrep_{next(_WR_COUNTER)}"
        self.workflow_id = workflow_id
        self.name = name
        self.stages_executed: List[str] = []
        self.stages_failed: List[str] = []
        self.total_duration_ms: float = 0.0
        self.success: bool = True
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
        self.stage_details: List[Dict[str, Any]] = []
        self.timestamp: float = time.time()

    def add_stage(self, stage_id: str, layer: str, status: str,
                  duration_ms: float = 0.0, error: str = "") -> None:
        detail = {
            "stage_id": stage_id, "layer": layer, "status": status,
            "duration_ms": round(duration_ms, 1), "error": error,
        }
        self.stage_details.append(detail)
        if status == "completed":
            if layer not in self.stages_executed:
                self.stages_executed.append(layer)
        elif status == "failed":
            self.stages_failed.append(layer)
            self.success = False
            if error:
                self.warnings.append(f"{layer}: {error}")

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def add_recommendation(self, recommendation: str) -> None:
        self.recommendations.append(recommendation)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "workflow_id": self.workflow_id,
            "success": self.success,
            "stages_executed": len(self.stages_executed),
            "stages_failed": len(self.stages_failed),
            "total_duration_ms": round(self.total_duration_ms, 1),
            "warning_count": len(self.warnings),
            "recommendation_count": len(self.recommendations),
        }

    def export_dict(self) -> Dict[str, Any]:
        return {
            **self.get_summary(),
            "stages_executed": self.stages_executed,
            "stages_failed": self.stages_failed,
            "stage_details": self.stage_details,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }
