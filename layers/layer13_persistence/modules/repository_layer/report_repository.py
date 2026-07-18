"""report_repository.py — Report repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class ReportEntity(BaseEntity):
    __slots__ = ("report_type", "title", "content", "generated_at")

    def __init__(self, report_type: str, title: str) -> None:
        super().__init__()
        self.report_type = report_type
        self.title = title
        self.content: Dict[str, Any] = {}
        self.generated_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"type": self.report_type, "title": self.title})
        return base


class ReportRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("report")

    def find_by_type(self, report_type: str) -> List[ReportEntity]:
        return self.find(report_type=report_type)
