"""Orchestrator Report — Generate final execution reports."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_OR_COUNTER = itertools.count(1)


class OrchestratorReport:
    """Final report from an orchestration run."""

    __slots__ = ("report_id", "request_id", "layers_executed", "layers_failed",
                 "duration_ms", "success", "warnings", "recommendations",
                 "layer_outputs", "metrics", "timestamp")

    def __init__(self, request_id: str = "") -> None:
        self.report_id: str = f"orep_{next(_OR_COUNTER)}"
        self.request_id = request_id
        self.layers_executed: List[str] = []
        self.layers_failed: List[str] = []
        self.duration_ms: float = 0.0
        self.success: bool = True
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
        self.layer_outputs: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}
        self.timestamp: float = time.time()

    def add_layer_output(self, layer: str, output: Any) -> None:
        self.layer_outputs[layer] = output
        if layer not in self.layers_executed:
            self.layers_executed.append(layer)

    def add_failure(self, layer: str, error: str = "") -> None:
        self.layers_failed.append(layer)
        self.success = False
        self.warnings.append(f"Layer {layer} failed: {error}")

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def add_recommendation(self, recommendation: str) -> None:
        self.recommendations.append(recommendation)

    def set_metrics(self, metrics: Dict[str, Any]) -> None:
        self.metrics = dict(metrics)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "request_id": self.request_id,
            "success": self.success,
            "layers_executed": len(self.layers_executed),
            "layers_failed": len(self.layers_failed),
            "duration_ms": round(self.duration_ms, 1),
            "warning_count": len(self.warnings),
            "recommendation_count": len(self.recommendations),
        }

    def export_dict(self) -> Dict[str, Any]:
        return {
            **self.get_summary(),
            "layers_executed": self.layers_executed,
            "layers_failed": self.layers_failed,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "metrics": self.metrics,
        }
