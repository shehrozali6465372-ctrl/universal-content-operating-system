"""RuntimeFactory — Factory for creating runtime components."""
from __future__ import annotations
from typing import Any, Dict

from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_manager import RuntimeManager
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_config import RuntimeConfig


class RuntimeFactory:
    """Factory for creating RuntimeManager with predefined configurations."""

    PRESETS = {
        "development": {"max_workers": 2, "task_timeout": 60, "enable_profiling": True},
        "production": {"max_workers": 10, "task_timeout": 300, "enable_monitoring": True},
        "high_performance": {"max_workers": 20, "task_timeout": 120, "batch_size": 100},
        "minimal": {"max_workers": 1, "task_timeout": 30, "queue_size": 100},
    }

    @classmethod
    def create(cls, preset: str = "production") -> RuntimeManager:
        config_dict = cls.PRESETS.get(preset, cls.PRESETS["production"])
        config = RuntimeConfig.from_dict(config_dict)
        return RuntimeManager(config)

    @classmethod
    def create_custom(cls, config_dict: Dict[str, Any]) -> RuntimeManager:
        config = RuntimeConfig.from_dict(config_dict)
        return RuntimeManager(config)

    @classmethod
    def get_presets(cls) -> Dict[str, Dict[str, Any]]:
        return dict(cls.PRESETS)
