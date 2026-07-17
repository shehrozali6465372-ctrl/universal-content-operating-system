"""Threshold Manager — Manage quality thresholds for different contexts."""
from __future__ import annotations
from typing import Any, Dict


class ThresholdConfig:
    """A threshold configuration for a specific context."""

    __slots__ = ("context", "metric", "min_threshold", "warning_threshold",
                 "target_threshold", "hard_stop")

    def __init__(self, context: str = "default", metric: str = "quality") -> None:
        self.context = context
        self.metric = metric
        self.min_threshold: float = 0.3
        self.warning_threshold: float = 0.6
        self.target_threshold: float = 0.8
        self.hard_stop: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context": self.context,
            "metric": self.metric,
            "min_threshold": self.min_threshold,
            "warning_threshold": self.warning_threshold,
            "target_threshold": self.target_threshold,
            "hard_stop": self.hard_stop,
        }


class ThresholdManager:
    """Manage quality thresholds with context-aware overrides."""

    DEFAULT_THRESHOLDS = {
        "quality": ThresholdConfig("default", "quality"),
        "safety": ThresholdConfig("default", "safety"),
        "seo": ThresholdConfig("default", "seo"),
        "engagement": ThresholdConfig("default", "engagement"),
    }

    def __init__(self) -> None:
        self._configs: Dict[str, ThresholdConfig] = dict(self.DEFAULT_THRESHOLDS)
        self._contexts: Dict[str, Dict[str, ThresholdConfig]] = {}

    def set_threshold(self, config: ThresholdConfig) -> None:
        self._configs[config.metric] = config

    def set_context_threshold(self, context: str, config: ThresholdConfig) -> None:
        self._contexts.setdefault(context, {})[config.metric] = config

    def get_threshold(self, metric: str = "quality",
                      context: str = "default") -> ThresholdConfig:
        if context in self._contexts and metric in self._contexts[context]:
            return self._contexts[context][metric]
        return self._configs.get(metric, ThresholdConfig("default", metric))

    def evaluate(self, metric: str, value: float,
                 context: str = "default") -> Dict[str, Any]:
        config = self.get_threshold(metric, context)
        result = {
            "metric": metric,
            "value": value,
            "context": context,
            "status": "pass",
            "threshold": config.min_threshold,
        }
        if value < config.min_threshold:
            result["status"] = "fail"
            if config.hard_stop:
                result["status"] = "hard_stop"
        elif value < config.warning_threshold:
            result["status"] = "warning"
        elif value >= config.target_threshold:
            result["status"] = "excellent"
        return result

    def get_configs(self) -> Dict[str, ThresholdConfig]:
        return dict(self._configs)

    def get_context_configs(self, context: str) -> Dict[str, ThresholdConfig]:
        return dict(self._contexts.get(context, {}))
