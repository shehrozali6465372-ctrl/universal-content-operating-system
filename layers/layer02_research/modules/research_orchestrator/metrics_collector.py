"""
Metrics Collector
Layer 2: Research Engine — Module 10

Collects and aggregates execution metrics:
- Module-level metrics
- Execution-level metrics
- Performance analysis
- Report generation
"""

from datetime import datetime, timezone
from typing import Dict, List

from layers.layer02_research.modules.research_orchestrator.execution_context import ExecutionContext


class ModuleMetrics:
    """Metrics for a single module execution."""

    __slots__ = (
        "module", "duration_sec", "api_calls", "memory_mb",
        "success", "confidence", "retry_count", "error",
    )

    def __init__(self, module: str):
        self.module = module
        self.duration_sec = 0.0
        self.api_calls = 0
        self.memory_mb = 0.0
        self.success = True
        self.confidence = 0.0
        self.retry_count = 0
        self.error = ""

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "duration_sec": round(self.duration_sec, 3),
            "api_calls": self.api_calls,
            "memory_mb": round(self.memory_mb, 2),
            "success": self.success,
            "confidence": round(self.confidence, 3),
            "retry_count": self.retry_count,
            "error": self.error,
        }


class MetricsCollector:
    """Collects and aggregates metrics for research executions."""

    def __init__(self):
        self._module_metrics: Dict[str, List[ModuleMetrics]] = {}
        self._execution_metrics: List[Dict] = []

    def record_module(
        self,
        module: str,
        duration_sec: float = 0.0,
        api_calls: int = 0,
        memory_mb: float = 0.0,
        success: bool = True,
        confidence: float = 0.0,
        retry_count: int = 0,
        error: str = "",
    ) -> ModuleMetrics:
        """Record metrics for a module execution."""
        m = ModuleMetrics(module)
        m.duration_sec = duration_sec
        m.api_calls = api_calls
        m.memory_mb = memory_mb
        m.success = success
        m.confidence = confidence
        m.retry_count = retry_count
        m.error = error

        if module not in self._module_metrics:
            self._module_metrics[module] = []
        self._module_metrics[module].append(m)
        return m

    def record_execution(self, context: ExecutionContext) -> Dict:
        """Record metrics for a complete execution."""
        total_modules = (
            len(context.completed_modules)
            + len(context.failed_modules)
            + len(context.skipped_modules)
        )

        execution_metrics = {
            "execution_id": context.execution_id,
            "topic": context.topic,
            "status": context.status,
            "total_modules": total_modules,
            "completed": len(context.completed_modules),
            "failed": len(context.failed_modules),
            "skipped": len(context.skipped_modules),
            "overall_confidence": context.overall_confidence,
            "total_duration_sec": context.total_duration_sec,
            "total_api_calls": context.total_api_calls,
            "success_rate": (
                round(len(context.completed_modules) / max(total_modules, 1), 3)
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._execution_metrics.append(execution_metrics)
        return execution_metrics

    def get_module_stats(self, module: str) -> Dict:
        """Get aggregated stats for a module across all executions."""
        records = self._module_metrics.get(module, [])
        if not records:
            return {"module": module, "executions": 0}

        total = len(records)
        successful = sum(1 for r in records if r.success)
        avg_duration = sum(r.duration_sec for r in records) / total
        avg_confidence = sum(r.confidence for r in records) / total
        total_api = sum(r.api_calls for r in records)
        total_retries = sum(r.retry_count for r in records)

        return {
            "module": module,
            "executions": total,
            "success_rate": round(successful / total, 3),
            "avg_duration_sec": round(avg_duration, 3),
            "avg_confidence": round(avg_confidence, 3),
            "total_api_calls": total_api,
            "total_retries": total_retries,
        }

    def get_all_stats(self) -> Dict[str, Dict]:
        """Get stats for all modules."""
        return {
            module: self.get_module_stats(module)
            for module in self._module_metrics
        }

    def get_execution_summary(self) -> Dict:
        """Get summary of all executions."""
        if not self._execution_metrics:
            return {"total_executions": 0}

        total = len(self._execution_metrics)
        successful = sum(
            1 for e in self._execution_metrics if e["status"] == "completed"
        )
        avg_confidence = sum(
            e["overall_confidence"] for e in self._execution_metrics
        ) / total

        return {
            "total_executions": total,
            "successful": successful,
            "success_rate": round(successful / total, 3),
            "avg_confidence": round(avg_confidence, 3),
        }

    def get_slowest_modules(self, top_n: int = 5) -> List[Dict]:
        """Get the slowest modules by average duration."""
        stats = []
        for module in self._module_metrics:
            s = self.get_module_stats(module)
            if s["executions"] > 0:
                stats.append(s)
        stats.sort(key=lambda x: x.get("avg_duration_sec", 0), reverse=True)
        return stats[:top_n]

    def reset(self):
        """Clear all metrics."""
        self._module_metrics.clear()
        self._execution_metrics.clear()
