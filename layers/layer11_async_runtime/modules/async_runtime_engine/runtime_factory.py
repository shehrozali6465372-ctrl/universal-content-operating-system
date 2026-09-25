"""RuntimeFactory — safe creation of predefined runtime configurations."""
from __future__ import annotations

from typing import Any, Dict

from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_config import RuntimeConfig
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_manager import RuntimeManager


class RuntimeFactory:
    """Factory for RuntimeManager instances with explicit presets."""

    PRESETS = {
        "development": {"max_workers": 2, "task_timeout": 60, "enable_profiling": True},
        "production": {"max_workers": 10, "task_timeout": 300, "enable_monitoring": True},
        "high_performance": {"max_workers": 20, "task_timeout": 120, "batch_size": 100},
        "minimal": {"max_workers": 1, "task_timeout": 30, "queue_size": 100},
    }

    @classmethod
    def create(cls, preset: str = "production") -> RuntimeManager:
        if not isinstance(preset, str) or preset not in cls.PRESETS:
            raise ValueError(f"unknown runtime preset: {preset!r}")
        return RuntimeManager(RuntimeConfig.from_dict(cls.PRESETS[preset]))

    @classmethod
    def create_custom(cls, config_dict: Dict[str, Any]) -> RuntimeManager:
        return RuntimeManager(RuntimeConfig.from_dict(config_dict))

    @classmethod
    def get_presets(cls) -> Dict[str, Dict[str, Any]]:
        return {name: dict(values) for name, values in cls.PRESETS.items()}
