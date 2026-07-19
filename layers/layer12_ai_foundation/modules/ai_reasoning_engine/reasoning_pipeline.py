"""ReasoningPipeline — pipeline for multi-stage reasoning."""
from __future__ import annotations

from typing import Any, Callable, Dict, List



class ReasoningPipeline:
    """Pipeline for multi-stage reasoning operations."""

    def __init__(self) -> None:
        self._stages: List[Dict[str, Any]] = []

    def add_stage(self, name: str, handler: Callable, **kwargs: Any) -> "ReasoningPipeline":
        self._stages.append({"name": name, "handler": handler, "config": kwargs})
        return self

    def execute(self, input_data: Any) -> Dict[str, Any]:
        current = input_data
        results: List[Dict[str, Any]] = []
        for stage in self._stages:
            try:
                output = stage["handler"](current)
                results.append({"stage": stage["name"], "output": str(output)[:200], "success": True})
                current = output
            except Exception as exc:
                results.append({"stage": stage["name"], "error": str(exc), "success": False})
                break
        return {"final_output": current, "stages": results, "completed": len(results)}

    def stage_count(self) -> int:
        return len(self._stages)

    def clear(self) -> None:
        self._stages.clear()
