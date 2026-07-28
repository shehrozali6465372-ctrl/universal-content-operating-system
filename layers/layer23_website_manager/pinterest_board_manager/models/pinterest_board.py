"""PinterestBoard — Core data model for a Pinterest Board."""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class BoardStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DISABLED = "disabled"
    PENDING = "pending"


@dataclass
class PinterestBoard:
    """Complete Pinterest Board with SEO, performance and metadata."""

    # Identity
    board_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    account_id: str = ""
    board_name: str = ""
    board_description: str = ""
    niche: str = ""
    category: str = "other"

    # SEO
    seo_title: str = ""
    seo_description: str = ""
    keywords: List[str] = field(default_factory=list)
    search_terms: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    seo_score: float = 0.0

    # Structure
    parent_board_id: Optional[str] = None
    sort_order: int = 0
    board_depth: int = 0

    # Permissions
    can_edit: List[str] = field(default_factory=lambda: ["owner"])
    can_publish: List[str] = field(default_factory=lambda: ["owner"])

    # Stats
    pin_count: int = 0
    total_impressions: int = 0
    total_saves: int = 0
    total_clicks: int = 0
    engagement_rate: float = 0.0

    # Status
    status: BoardStatus = BoardStatus.PENDING
    is_archived: bool = False
    is_ai_created: bool = False
    ai_recommended: bool = False
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def display_name(self) -> str:
        return self.seo_title or self.board_name

    @property
    def is_empty(self) -> bool:
        return self.pin_count == 0

    @property
    def is_active(self) -> bool:
        return self.status == BoardStatus.ACTIVE and not self.is_archived

    def to_dict(self) -> Dict[str, Any]:
        return {
            "board_id": self.board_id,
            "account_id": self.account_id,
            "board_name": self.board_name,
            "board_description": self.board_description[:100] if self.board_description else "",
            "niche": self.niche,
            "category": self.category,
            "seo_title": self.seo_title,
            "seo_score": round(self.seo_score, 1),
            "keywords": self.keywords[:10],
            "hashtags": self.hashtags[:10],
            "parent_board_id": self.parent_board_id,
            "sort_order": self.sort_order,
            "pin_count": self.pin_count,
            "total_impressions": self.total_impressions,
            "total_saves": self.total_saves,
            "total_clicks": self.total_clicks,
            "engagement_rate": round(self.engagement_rate, 2),
            "status": self.status.value,
            "is_archived": self.is_archived,
            "is_ai_created": self.is_ai_created,
            "is_empty": self.is_empty,
            "created_at": self.created_at,
        }
