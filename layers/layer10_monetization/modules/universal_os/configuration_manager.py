"""ConfigurationManager — System settings, models, limits, budgets, features."""
from __future__ import annotations
from typing import Any, Dict, Optional


class ConfigurationManager:
    """Manage system settings, models, limits, budgets, and feature flags."""

    def __init__(self) -> None:
        self._settings: Dict[str, Any] = {
            "system_name": "Universal AI Content Agent",
            "version": "1.0.0",
            "max_concurrent_tasks": 5,
            "default_language": "en",
            "timezone": "UTC",
        }
        self._models: Dict[str, Dict[str, Any]] = {}
        self._limits: Dict[str, int] = {
            "max_requests_per_minute": 60,
            "max_tokens_per_request": 4096,
            "max_image_size_mb": 10,
            "max_video_length_seconds": 600,
        }
        self._budgets: Dict[str, float] = {
            "daily_api_budget": 100.0,
            "monthly_api_budget": 2000.0,
        }
        self._features: Dict[str, bool] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def get_all(self) -> Dict[str, Any]:
        return dict(self._settings)

    def register_model(self, name: str, config: Dict[str, Any]) -> None:
        self._models[name] = dict(config)

    def get_model(self, name: str) -> Optional[Dict[str, Any]]:
        return self._models.get(name)

    def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._models)

    def get_limit(self, key: str, default: int = 0) -> int:
        return self._limits.get(key, default)

    def set_limit(self, key: str, value: int) -> None:
        self._limits[key] = value

    def get_budget(self, key: str, default: float = 0.0) -> float:
        return self._budgets.get(key, default)

    def set_budget(self, key: str, value: float) -> None:
        self._budgets[key] = value

    def enable_feature(self, feature: str) -> None:
        self._features[feature] = True

    def disable_feature(self, feature: str) -> None:
        self._features[feature] = False

    def is_feature_enabled(self, feature: str) -> bool:
        return self._features.get(feature, False)

    def get_all_features(self) -> Dict[str, bool]:
        return dict(self._features)

    def get_stats(self) -> Dict[str, Any]:
        return {"settings": len(self._settings), "models": len(self._models),
                "limits": len(self._limits), "budgets": len(self._budgets),
                "features": len(self._features)}
