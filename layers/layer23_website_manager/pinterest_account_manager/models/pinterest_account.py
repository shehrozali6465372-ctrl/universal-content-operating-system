"""PinterestAccount — Core data model for a Pinterest Business Account."""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class AccountStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AuthStatus(str, Enum):
    AUTHENTICATED = "authenticated"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
    FAILED = "failed"


@dataclass
class PinterestAccount:
    """Complete Pinterest Business Account with all metadata."""

    # Identity
    account_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    account_name: str = ""
    username: str = ""
    niche: str = ""
    business_name: str = ""

    # Profile
    profile_image: str = ""
    banner: str = ""
    description: str = ""
    website: str = ""
    contact_email: str = ""
    contact_phone: str = ""

    # Branding
    brand_colors: Dict[str, str] = field(default_factory=lambda: {
        "primary": "#E60023",
        "secondary": "#000000",
    })
    brand_logo: str = ""
    brand_banner: str = ""
    voice_profile: str = "professional"
    brand_consistency_score: float = 0.0

    # Website Claim
    website_claimed: bool = False
    claim_status: str = "not_claimed"  # not_claimed, pending, verified, failed
    verification_method: str = ""

    # Authentication
    access_token: str = ""
    refresh_token: str = ""
    token_expiry: float = 0.0
    auth_status: AuthStatus = AuthStatus.PENDING
    last_auth_at: float = 0.0

    # Permissions
    can_post: bool = True
    can_view_analytics: bool = True
    can_access_api: bool = True
    can_manage_boards: bool = True
    custom_permissions: Dict[str, bool] = field(default_factory=dict)

    # Health
    health_score: float = 100.0
    is_suspended: bool = False
    is_restricted: bool = False
    last_health_check: float = 0.0
    health_issues: List[str] = field(default_factory=list)
    consecutive_errors: int = 0
    total_posts: int = 0
    total_errors: int = 0
    last_post_at: float = 0.0

    # Metrics
    follower_count: int = 0
    monthly_views: int = 0
    engagement_rate: float = 0.0

    # Status
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # Metadata
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "username": self.username,
            "niche": self.niche,
            "business_name": self.business_name,
            "profile_image": self.profile_image,
            "banner": self.banner,
            "description": self.description,
            "website": self.website,
            "website_claimed": self.website_claimed,
            "claim_status": self.claim_status,
            "brand_colors": self.brand_colors,
            "voice_profile": self.voice_profile,
            "brand_consistency_score": round(self.brand_consistency_score, 1),
            "auth_status": self.auth_status.value,
            "token_expiry": self.token_expiry,
            "can_post": self.can_post,
            "can_view_analytics": self.can_view_analytics,
            "health_score": round(self.health_score, 1),
            "is_suspended": self.is_suspended,
            "is_restricted": self.is_restricted,
            "health_issues": self.health_issues,
            "total_posts": self.total_posts,
            "total_errors": self.total_errors,
            "follower_count": self.follower_count,
            "monthly_views": self.monthly_views,
            "engagement_rate": round(self.engagement_rate, 2),
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @property
    def display_name(self) -> str:
        return self.business_name or self.account_name or self.username

    @property
    def is_healthy(self) -> bool:
        return (self.health_score >= 60
                and self.status == AccountStatus.ACTIVE
                and not self.is_suspended
                and self.auth_status == AuthStatus.AUTHENTICATED)

    @property
    def error_rate(self) -> float:
        total = self.total_posts + self.total_errors
        if total == 0:
            return 0.0
        return round((self.total_errors / total) * 100, 1)
