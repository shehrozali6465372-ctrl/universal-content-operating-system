"""analytics_repository.py — Analytics repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class AnalyticsEntity(BaseEntity):
    __slots__ = ("metric_name", "value", "platform", "period")

    def __init__(self, metric_name: str, value: float = 0.0, platform: str = "") -> None:
        super().__init__()
        self.metric_name = metric_name
        self.value = value
        self.platform = platform
        self.period: str = "daily"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"metric": self.metric_name, "value": self.value,
                      "platform": self.platform})
        return base


class AnalyticsRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("analytics")

    def find_by_metric(self, metric_name: str) -> List[AnalyticsEntity]:
        return self.find(metric_name=metric_name)

    def find_by_platform(self, platform: str) -> List[AnalyticsEntity]:
        return self.find(platform=platform)

    def get_metric_total(self, metric_name: str) -> float:
        return sum(e.value for e in self.find(metric_name=metric_name))
