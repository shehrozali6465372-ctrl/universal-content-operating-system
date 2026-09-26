"""Production pipeline runner for Layer 06 quality checks."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Mapping, Set

from layers.layer06_quality.modules.quality_orchestrator.quality_report import (
    ModuleExecutionRecord,
)


MODULE_PIPELINE = (
    {"name": "content_quality", "phase": 1, "required": True},
    {"name": "fact_validation", "phase": 1, "required": True},
    {"name": "safety", "phase": 1, "required": True},
    {"name": "originality", "phase": 2, "required": True},
    {"name": "seo", "phase": 2, "required": True},
    {"name": "platform_compliance", "phase": 2, "required": True},
    {"name": "brand_voice", "phase": 2, "required": True},
    # Human review is a conditional gate and is intentionally not required
    # for every automated run.
    {"name": "human_review", "phase": 3, "required": False},
)


class PipelineRunner:
    """Execute the Layer 06 pipeline with bounded, observable retries."""

    def __init__(self, max_retries: int = 2, retry_delay_seconds: float = 0.01) -> None:
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be non-negative")
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._execution_count = 0

    def run_module(
        self,
        name: str,
        func: Callable[..., Any],
        context: Mapping[str, Any] | None = None,
        retries: int | None = None,
    ) -> ModuleExecutionRecord:
        """Execute a module, retaining the final failure without hiding it."""
        if not name:
            raise ValueError("module name is required")
        if not callable(func):
            raise TypeError(f"module '{name}' is not callable")

        retry_count = self._max_retries if retries is None else retries
        if retry_count < 0:
            raise ValueError("retries must be non-negative")

        record = ModuleExecutionRecord(name)
        record.status = "running"
        start = time.monotonic()
        last_error: Exception | None = None

        for attempt in range(retry_count + 1):
            try:
                result = func(**dict(context or {}))
                record.status = "completed"
                if isinstance(result, dict):
                    record.score = float(result.get("score", 0.0))
                    record.confidence = float(result.get("confidence", 0.0))
                    record.issues_count = int(result.get("issues_count", 0))
                break
            except Exception as exc:  # module isolation boundary
                last_error = exc
                if attempt < retry_count and self._retry_delay_seconds:
                    time.sleep(self._retry_delay_seconds)

        if record.status != "completed":
            record.status = "failed"
            record.error_message = (
                f"{type(last_error).__name__}: {last_error}"
            )[:200]

        record.duration_ms = round((time.monotonic() - start) * 1000, 2)
        self._execution_count += 1
        return record

    def run_pipeline(
        self,
        module_funcs: Mapping[str, Callable[..., Any]],
        context: Mapping[str, Any],
    ) -> List[ModuleExecutionRecord]:
        """Run every required module and explicitly mark optional omissions."""
        records: List[ModuleExecutionRecord] = []
        configured: Set[str] = set(module_funcs)

        for mod in MODULE_PIPELINE:
            name = mod["name"]
            func = module_funcs.get(name)
            if func is None:
                record = ModuleExecutionRecord(name)
                if mod["required"]:
                    record.status = "failed"
                    record.error_message = "required module is not configured"
                else:
                    record.status = "skipped"
                records.append(record)
                continue

            records.append(self.run_module(name, func, context))

        return records

    def get_slowest_modules(
        self, records: List[ModuleExecutionRecord],
    ) -> List[ModuleExecutionRecord]:
        """Return modules sorted by duration (slowest first)."""
        return sorted(records, key=lambda r: r.duration_ms, reverse=True)

    def get_failed_modules(
        self, records: List[ModuleExecutionRecord],
    ) -> List[ModuleExecutionRecord]:
        """Return only failed modules."""
        return [r for r in records if r.status == "failed"]

    @property
    def execution_count(self) -> int:
        return self._execution_count
