"""BoardPerformance — Daily performance metrics for a Pinterest board."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class BoardPerformance:
    """Daily performance snapshot for a Pinterest board."""

    performance_id: str = field(default_factory=lambda: __import__("uuid").uuid4().hex[:12])
    board_id: str = ""
    date: float = field(default_factory=time.time)

    impressions: int = 0
    saves: int = 0
    clicks: int = 0
    closeups: int = 0
    engagement: int = 0

    @property
    def engagement_rate(self) -> float:
        total = self.impressions or 1
        engaged = self.saves + self.clicks + self.closeups
        return round((engaged / total) * 100, 2)

    @property
    def save_rate(self) -> float:
        total = self.impressions or 1
        return round((self.saves / total) * 100, 2)

    @property
    def click_rate(self) -> float:
        total = self.impressions or 1
        return round((self.clicks / total) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "performance_id": self.performance_id,
            "board_id": self.board_id,
            "date": self.date,
            "impressions": self.impressions,
            "saves": self.saves,
            "clicks": self.clicks,
            "closeups": self.closeups,
            "engagement_rate": self.engagement_rate,
            "save_rate": self.save_rate,
            "click_rate": self.click_rate,
        }

    @classmethod
    def aggregate(cls, performances: list["BoardPerformance"]) -> "BoardPerformance":
        """Aggregate multiple performances into one."""
        if not performances:
            return cls()
        return cls(
            impressions=sum(p.impressions for p in performances),
            saves=sum(p.saves for p in performances),
            clicks=sum(p.clicks for p in performances),
            closeups=sum(p.closeups for p in performances),
            engagement=sum(p.engagement for p in performances),
        )
