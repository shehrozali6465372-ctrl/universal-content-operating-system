"""Pipeline Monitor — Track pipeline execution health and progress."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class ExecutionRecord:
    """Record of a pipeline execution."""

    __slots__ = ("pipeline_name", "success", "total_duration_ms",
                 "completed_stages", "failed_stages", "timestamp")

    def __init__(self, pipeline_name: str = "", success: bool = False) -> None:
        self.pipeline_name = pipeline_name
        self.success = success
        self.total_duration_ms: float = 0.0
        self.completed_stages: int = 0
        self.failed_stages: int = 0
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_name": self.pipeline_name,
            "success": self.success,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "completed_stages": self.completed_stages,
            "failed_stages": self.failed_stages,
            "timestamp": self.timestamp,
        }


class PipelineMonitor:
    """Monitor pipeline execution health."""

    def __init__(self) -> None:
        self._records: List[ExecutionRecord] = []
        self._total_executions = 0
        self._total_success = 0
        self._total_duration_ms = 0.0

    def record_execution(self, record: ExecutionRecord) -> None:
        self._records.append(record)
        self._total_executions += 1
        if record.success:
            self._total_success += 1
        self._total_duration_ms += record.total_duration_ms

    def get_health(self) -> Dict[str, Any]:
        success_rate = self._total_success / max(1, self._total_executions)
        avg_duration = self._total_duration_ms / max(1, self._total_executions)
        return {
            "total_executions": self._total_executions,
            "success_rate": round(success_rate, 3),
            "avg_duration_ms": round(avg_duration, 2),
            "status": "healthy" if success_rate >= 0.9 else "degraded",
        }

    def get_recent(self, count: int = 10) -> List[ExecutionRecord]:
        return list(self._records[-count:])

    def get_records(self, success_only: bool = False) -> List[ExecutionRecord]:
        if success_only:
            return [r for r in self._records if r.success]
        return list(self._records)

    @property
    def execution_count(self) -> int:
        return self._total_executions
