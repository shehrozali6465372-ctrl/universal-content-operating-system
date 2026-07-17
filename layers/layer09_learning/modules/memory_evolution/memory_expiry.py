"""Memory Expiry — Manage memory expiration and refresh cycles."""
from __future__ import annotations
from typing import Any, Dict, List


class ExpiryPolicy:
    """Configuration for memory expiration."""

    __slots__ = ("category", "max_age_days", "refresh_on_usage", "auto_refresh")

    def __init__(self, category: str = "default", max_age_days: int = 90) -> None:
        self.category = category
        self.max_age_days = max_age_days
        self.refresh_on_usage: bool = True
        self.auto_refresh: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "max_age_days": self.max_age_days,
            "refresh_on_usage": self.refresh_on_usage,
        }


class ExpiryCheck:
    """Result of checking a memory entry for expiry."""

    __slots__ = ("entry_id", "is_expired", "age_days", "max_age",
                 "should_refresh", "action")

    def __init__(self, entry_id: str = "") -> None:
        self.entry_id = entry_id
        self.is_expired: bool = False
        self.age_days: float = 0.0
        self.max_age: float = 90.0
        self.should_refresh: bool = False
        self.action: str = "keep"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "is_expired": self.is_expired,
            "age_days": round(self.age_days, 1),
            "action": self.action,
        }


class MemoryExpiry:
    """Manage memory expiration policies and checks."""

    def __init__(self) -> None:
        self._policies: Dict[str, ExpiryPolicy] = {}
        self._checks: List[ExpiryCheck] = []
        self._refresh_count: int = 0
        self._default_policy = ExpiryPolicy("default", 90)

    def set_policy(self, policy: ExpiryPolicy) -> None:
        self._policies[policy.category] = policy

    def get_policy(self, category: str = "default") -> ExpiryPolicy:
        return self._policies.get(category, self._default_policy)

    def check_entry(self, entry_id: str, age_days: float, category: str = "default",
                    usage_count: int = 0) -> ExpiryCheck:
        policy = self.get_policy(category)
        check = ExpiryCheck(entry_id)
        check.age_days = age_days
        check.max_age = policy.max_age_days
        check.is_expired = age_days > policy.max_age_days
        if check.is_expired and policy.refresh_on_usage and usage_count > 0:
            check.should_refresh = True
            check.action = "refresh"
            self._refresh_count += 1
        elif check.is_expired:
            check.action = "expire"
        else:
            check.action = "keep"
        self._checks.append(check)
        return check

    def check_batch(self, entries: List[Dict[str, Any]]) -> List[ExpiryCheck]:
        results = []
        for e in entries:
            check = self.check_entry(
                entry_id=e.get("entry_id", ""),
                age_days=e.get("age_days", 0.0),
                category=e.get("category", "default"),
                usage_count=e.get("usage_count", 0),
            )
            results.append(check)
        return results

    def get_expired(self) -> List[ExpiryCheck]:
        return [c for c in self._checks if c.is_expired]

    def get_refreshable(self) -> List[ExpiryCheck]:
        return [c for c in self._checks if c.should_refresh]

    def get_checks(self) -> List[ExpiryCheck]:
        return list(self._checks)

    @property
    def refresh_count(self) -> int:
        return self._refresh_count
