"""PromptMetrics — track prompt performance and quality."""
from __future__ import annotations

import time
from typing import Any, Dict


class PromptMetrics:
    """Track metrics for prompt generation and optimization."""

    def __init__(self) -> None:
        self.total_prompts: int = 0
        self.total_optimizations: int = 0
        self.templates_used: Dict[str, int] = {}
        self.error_count: int = 0
        self.total_latency_ms: float = 0.0
        self._start_time = time.time()

    def record_prompt(self, template: str = "", latency_ms: float = 0.0) -> None:
        self.total_prompts += 1
        self.total_latency_ms += latency_ms
        if template:
            self.templates_used[template] = self.templates_used.get(template, 0) + 1

    def record_optimization(self) -> None:
        self.total_optimizations += 1

    def record_error(self) -> None:
        self.error_count += 1

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.total_prompts, 1)

    @property
    def error_rate(self) -> float:
        return self.error_count / max(self.total_prompts, 1)

    def reset(self) -> None:
        self.__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {"total_prompts": self.total_prompts,
                "total_optimizations": self.total_optimizations,
                "templates_used": self.templates_used,
                "error_rate": round(self.error_rate, 4),
                "avg_latency_ms": round(self.avg_latency_ms, 2)}
