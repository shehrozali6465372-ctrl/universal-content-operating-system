"""Pipeline Runner — Execute quality modules in correct dependency order."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List

from layers.layer06_quality.modules.quality_orchestrator.quality_report import ModuleExecutionRecord


# Module execution order with dependencies
MODULE_PIPELINE = [
    {"name": "content_quality", "phase": 1},
    {"name": "fact_validation", "phase": 1},
    {"name": "safety", "phase": 1},
    {"name": "originality", "phase": 2},
    {"name": "seo", "phase": 2},
    {"name": "platform_compliance", "phase": 2},
    {"name": "brand_voice", "phase": 2},
    {"name": "human_review", "phase": 3},
    {"name": "quality_scoring", "phase": 4},
]


class PipelineRunner:
    """Execute quality modules with retry support and metrics."""

    def __init__(self, max_retries: int = 2) -> None:
        self._max_retries = max_retries
        self._execution_count = 0

    def run_module(
        self,
        name: str,
        func: Callable[..., Any],
        context: Dict[str, Any],
        retries: int = 0,
    ) -> ModuleExecutionRecord:
        """Execute a single module with retry support."""
        record = ModuleExecutionRecord(name)
        record.status = "running"
        start = time.time()

        for attempt in range(retries + 1):
            try:
                result = func(**context) if context else func()
                record.status = "completed"
                if isinstance(result, dict):
                    record.score = result.get("score", 0.0)
                    record.confidence = result.get("confidence", 0.0)
                    record.issues_count = result.get("issues_count", 0)
                break
            except Exception as e:
                if attempt < retries:
                    time.sleep(0.01)  # Brief pause before retry
                    continue
                record.status = "failed"
                record.error_message = str(e)[:200]

        record.duration_ms = round((time.time() - start) * 1000, 2)
        self._execution_count += 1
        return record

    def run_pipeline(
        self,
        module_funcs: Dict[str, Callable],
        context: Dict[str, Any],
    ) -> List[ModuleExecutionRecord]:
        """Run all modules in pipeline order."""
        records: List[ModuleExecutionRecord] = []

        # Phase 1: Core quality checks (can be parallel in future)
        for mod in MODULE_PIPELINE:
            name = mod["name"]
            if name in module_funcs:
                record = self.run_module(
                    name, module_funcs[name], context, retries=self._max_retries,
                )
                records.append(record)
            else:
                record = ModuleExecutionRecord(name)
                record.status = "skipped"
                records.append(record)

        return records

    def get_slowest_modules(self, records: List[ModuleExecutionRecord]) -> List[ModuleExecutionRecord]:
        """Return modules sorted by duration (slowest first)."""
        return sorted(records, key=lambda r: r.duration_ms, reverse=True)

    def get_failed_modules(self, records: List[ModuleExecutionRecord]) -> List[ModuleExecutionRecord]:
        """Return only failed modules."""
        return [r for r in records if r.status == "failed"]

    @property
    def execution_count(self) -> int:
        return self._execution_count
