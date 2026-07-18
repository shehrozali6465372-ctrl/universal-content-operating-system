"""RuntimeBuilder — Fluent builder for RuntimeManager."""
from __future__ import annotations

from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_config import RuntimeConfig
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_manager import RuntimeManager


class RuntimeBuilder:
    """Fluent builder for creating configured RuntimeManager instances."""

    def __init__(self) -> None:
        self._config = RuntimeConfig()

    def max_workers(self, count: int) -> "RuntimeBuilder":
        self._config.max_workers = count
        return self

    def max_tasks(self, count: int) -> "RuntimeBuilder":
        self._config.max_tasks = count
        return self

    def task_timeout(self, seconds: float) -> "RuntimeBuilder":
        self._config.task_timeout = seconds
        return self

    def max_retries(self, count: int) -> "RuntimeBuilder":
        self._config.max_retries = count
        return self

    def enable_profiling(self) -> "RuntimeBuilder":
        self._config.enable_profiling = True
        return self

    def enable_monitoring(self) -> "RuntimeBuilder":
        self._config.enable_monitoring = True
        return self

    def log_level(self, level: str) -> "RuntimeBuilder":
        self._config.log_level = level
        return self

    def build(self) -> RuntimeManager:
        return RuntimeManager(self._config)
