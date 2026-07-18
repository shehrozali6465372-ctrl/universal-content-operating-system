"""RuntimeConfig — Configuration for the async runtime."""
from __future__ import annotations
from typing import Any, Dict


class RuntimeConfig:
    """Configuration for async runtime behavior."""

    __slots__ = ("max_workers", "max_tasks", "task_timeout",
                 "shutdown_timeout", "health_check_interval",
                 "metrics_interval", "max_retries", "retry_delay",
                 "queue_size", "batch_size", "enable_profiling",
                 "enable_monitoring", "log_level", "metadata")

    def __init__(self) -> None:
        self.max_workers: int = 10
        self.max_tasks: int = 1000
        self.task_timeout: float = 300.0
        self.shutdown_timeout: float = 30.0
        self.health_check_interval: float = 30.0
        self.metrics_interval: float = 60.0
        self.max_retries: int = 3
        self.retry_delay: float = 1.0
        self.queue_size: int = 10000
        self.batch_size: int = 50
        self.enable_profiling: bool = False
        self.enable_monitoring: bool = True
        self.log_level: str = "INFO"
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeConfig":
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
