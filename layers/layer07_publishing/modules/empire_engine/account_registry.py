"""AccountRegistry — Manages all social accounts, blogs, websites with metadata."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class AccountEntry:
    __slots__ = ("id", "platform", "username", "display_name", "email",
                 "niche", "language", "region", "status", "account_type",
                 "total_followers", "total_posts", "total_engagement",
                 "created_at", "last_active", "tags", "metadata",
                 "api_credentials", "daily_post_limit", "posts_today")

    PLATFORMS = ("facebook", "instagram", "tiktok", "x", "youtube", "pinterest",
                 "wordpress", "medium", "blogger", "devto", "hashnode", "linkedin",
                 "telegram", "threads", "bluesky")
    STATUSES = ("active", "paused", "banned", "shadow_banned", "pending", "expired")

    def __init__(self, platform: str, username: str, niche: str = "",
                 language: str = "en", region: str = "global",
                 account_type: str = "personal") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.platform = platform.lower()
        self.username = username
        self.display_name = ""
        self.email = ""
        self.niche = niche
        self.language = language
        self.region = region
        self.status = "active"
        self.account_type = account_type
        self.total_followers = 0
        self.total_posts = 0
        self.total_engagement = 0
        self.created_at = time.time()
        self.last_active = 0.0
        self.tags: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.api_credentials: Dict[str, str] = {}
        self.daily_post_limit = 5
        self.posts_today = 0

    @property
    def engagement_rate(self) -> float:
        if self.total_followers == 0 or self.total_posts == 0:
            return 0.0
        return (self.total_engagement / self.total_posts / self.total_followers) * 100

    @property
    def can_post(self) -> bool:
        return self.status == "active" and self.posts_today < self.daily_post_limit

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "platform": self.platform, "username": self.username,
            "display_name": self.display_name, "niche": self.niche,
            "language": self.language, "region": self.region,
            "status": self.status, "type": self.account_type,
            "followers": self.total_followers, "posts": self.total_posts,
            "engagement_rate": round(self.engagement_rate, 2),
            "daily_limit": self.daily_post_limit, "posts_today": self.posts_today,
            "can_post": self.can_post, "tags": self.tags,
        }


class AccountRegistry:
    """Central registry for all social accounts, blogs, and websites."""
    _instance: Optional["AccountRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "AccountRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._accounts: Dict[str, AccountEntry] = {}
        self._platform_index: Dict[str, List[str]] = {}
        self._niche_index: Dict[str, List[str]] = {}
        self._region_index: Dict[str, List[str]] = {}
        self._language_index: Dict[str, List[str]] = {}
        self._status_index: Dict[str, List[str]] = {}

    def register(self, platform: str, username: str, niche: str = "",
                 language: str = "en", region: str = "global",
                 account_type: str = "personal", daily_limit: int = 5,
                 tags: List[str] = None) -> AccountEntry:
        acc = AccountEntry(platform, username, niche, language, region, account_type)
        acc.daily_post_limit = daily_limit
        if tags:
            acc.tags = tags
        self._accounts[acc.id] = acc
        self._platform_index.setdefault(platform.lower(), []).append(acc.id)
        if niche:
            self._niche_index.setdefault(niche.lower(), []).append(acc.id)
        self._region_index.setdefault(region.lower(), []).append(acc.id)
        self._language_index.setdefault(language.lower(), []).append(acc.id)
        self._status_index.setdefault("active", []).append(acc.id)
        return acc

    def get_account(self, account_id: str) -> Optional[AccountEntry]:
        return self._accounts.get(account_id)

    def get_by_platform(self, platform: str) -> List[AccountEntry]:
        ids = self._platform_index.get(platform.lower(), [])
        return [self._accounts[i] for i in ids if i in self._accounts]

    def get_by_niche(self, niche: str) -> List[AccountEntry]:
        ids = self._niche_index.get(niche.lower(), [])
        return [self._accounts[i] for i in ids if i in self._accounts]

    def get_by_region(self, region: str) -> List[AccountEntry]:
        ids = self._region_index.get(region.lower(), [])
        return [self._accounts[i] for i in ids if i in self._accounts]

    def get_by_language(self, language: str) -> List[AccountEntry]:
        ids = self._language_index.get(language.lower(), [])
        return [self._accounts[i] for i in ids if i in self._accounts]

    def get_active_accounts(self) -> List[AccountEntry]:
        return [a for a in self._accounts.values() if a.status == "active"]

    def get_postable_accounts(self) -> List[AccountEntry]:
        return [a for a in self._accounts.values() if a.can_post]

    def update_status(self, account_id: str, status: str) -> bool:
        acc = self._accounts.get(account_id)
        if not acc or status not in AccountEntry.STATUSES:
            return False
        old_status = acc.status
        acc.status = status
        self._status_index.get(old_status, [])
        if account_id in self._status_index.get(old_status, []):
            self._status_index[old_status].remove(account_id)
        self._status_index.setdefault(status, []).append(account_id)
        return True

    def record_post(self, account_id: str) -> bool:
        acc = self._accounts.get(account_id)
        if acc and acc.can_post:
            acc.total_posts += 1
            acc.posts_today += 1
            acc.last_active = time.time()
            return True
        return False

    def reset_daily_counts(self) -> int:
        count = 0
        for acc in self._accounts.values():
            if acc.posts_today > 0:
                acc.posts_today = 0
                count += 1
        return count

    def get_registry_status(self) -> Dict[str, Any]:
        accounts = list(self._accounts.values())
        return {
            "total_accounts": len(accounts),
            "active": sum(1 for a in accounts if a.status == "active"),
            "paused": sum(1 for a in accounts if a.status == "paused"),
            "banned": sum(1 for a in accounts if a.status == "banned"),
            "shadow_banned": sum(1 for a in accounts if a.status == "shadow_banned"),
            "by_platform": {p: len(ids) for p, ids in self._platform_index.items()},
            "by_niche": {n: len(ids) for n, ids in self._niche_index.items()},
            "by_region": {r: len(ids) for r, ids in self._region_index.items()},
            "by_language": {l: len(ids) for l, ids in self._language_index.items()},
            "total_followers": sum(a.total_followers for a in accounts),
            "total_posts": sum(a.total_posts for a in accounts),
            "postable_now": len(self.get_postable_accounts()),
            "platforms_count": len(self._platform_index),
            "niches_count": len(self._niche_index),
            "regions_count": len(self._region_index),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "accounts": len(self._accounts),
            "platforms": len(self._platform_index),
            "niches": len(self._niche_index),
            "regions": len(self._region_index),
        }


def get_account_registry() -> AccountRegistry:
    return AccountRegistry()
