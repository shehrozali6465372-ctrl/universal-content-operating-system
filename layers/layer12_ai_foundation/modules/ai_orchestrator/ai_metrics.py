"""AIMetrics — track orchestrator metrics."""
from __future__ import annotations
import time
from typing import Any, Dict

class AIMetrics:
    def __init__(self) -> None:
        self.total_tasks: int = 0; self.completed: int = 0; self.failed: int = 0
        self.total_latency_ms: float = 0.0; self.by_component: Dict[str, int] = {}
        self._start = time.time()
    def record_task(self, component: str, success: bool, latency_ms: float = 0.0) -> None:
        self.total_tasks += 1
        if success: self.completed += 1
        else: self.failed += 1
        self.total_latency_ms += latency_ms
        self.by_component[component] = self.by_component.get(component, 0) + 1
    @property
    def success_rate(self) -> float: return self.completed / max(self.total_tasks, 1)
    @property
    def avg_latency(self) -> float: return self.total_latency_ms / max(self.total_tasks, 1)
    @property
    def uptime(self) -> float: return time.time() - self._start
    def reset(self) -> None: self.__init__()
    def to_dict(self) -> Dict[str, Any]:
        return {"total_tasks": self.total_tasks, "completed": self.completed, "failed": self.failed,
                "success_rate": round(self.success_rate, 4), "avg_latency_ms": round(self.avg_latency, 2),
                "uptime": round(self.uptime, 2), "by_component": self.by_component}
