"""AccountAssignmentEngine — Assigns niches to accounts with workload balancing."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional

from .account_registry import AccountRegistry, AccountEntry, get_account_registry


class AssignmentRule:
    __slots__ = ("id", "niche", "platforms", "languages", "regions",
                 "max_accounts", "priority", "active")

    def __init__(self, niche: str, platforms: List[str] = None,
                 languages: List[str] = None, regions: List[str] = None,
                 max_accounts: int = 100, priority: int = 5) -> None:
        self.id = f"rule_{int(time.time() * 1000)}"
        self.niche = niche
        self.platforms = platforms or []
        self.languages = languages or []
        self.regions = regions or []
        self.max_accounts = max_accounts
        self.priority = priority
        self.active = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "niche": self.niche,
            "platforms": self.platforms, "languages": self.languages,
            "regions": self.regions, "max_accounts": self.max_accounts,
            "priority": self.priority, "active": self.active,
        }


class WorkloadInfo:
    __slots__ = ("account_id", "username", "platform", "niche",
                 "posts_today", "daily_limit", "utilization", "available_slots")

    def __init__(self, acc: AccountEntry) -> None:
        self.account_id = acc.id
        self.username = acc.username
        self.platform = acc.platform
        self.niche = acc.niche
        self.posts_today = acc.posts_today
        self.daily_limit = acc.daily_post_limit
        self.utilization = (acc.posts_today / acc.daily_post_limit * 100) if acc.daily_post_limit > 0 else 0
        self.available_slots = max(0, acc.daily_post_limit - acc.posts_today)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id, "username": self.username,
            "platform": self.platform, "niche": self.niche,
            "posts_today": self.posts_today, "daily_limit": self.daily_limit,
            "utilization": round(self.utilization, 1),
            "available_slots": self.available_slots,
        }


class AccountAssignmentEngine:
    """Assigns niches to accounts and balances workload across accounts."""
    _instance: Optional["AccountAssignmentEngine"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "AccountAssignmentEngine":
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
        self._registry = get_account_registry()
        self._rules: Dict[str, AssignmentRule] = {}
        self._assignments: Dict[str, str] = {}
        self._history: List[Dict[str, Any]] = []

    def add_rule(self, niche: str, platforms: List[str] = None,
                 languages: List[str] = None, regions: List[str] = None,
                 max_accounts: int = 100, priority: int = 5) -> AssignmentRule:
        rule = AssignmentRule(niche, platforms, languages, regions, max_accounts, priority)
        self._rules[rule.id] = rule
        return rule

    def get_rule(self, rule_id: str) -> Optional[AssignmentRule]:
        return self._rules.get(rule_id)

    def assign_niche(self, account_id: str, niche: str) -> bool:
        acc = self._registry.get_account(account_id)
        if not acc:
            return False
        acc.niche = niche
        self._registry._niche_index.setdefault(niche.lower(), []).append(account_id)
        self._assignments[account_id] = niche
        self._history.append({
            "action": "assign", "account_id": account_id,
            "niche": niche, "timestamp": time.time(),
        })
        return True

    def auto_assign(self, niche: str, limit: int = 10) -> List[AccountEntry]:
        unassigned = [
            a for a in self._registry.get_active_accounts()
            if not a.niche and a.status == "active"
        ]
        assigned = []
        for acc in unassigned[:limit]:
            acc.niche = niche
            self._registry._niche_index.setdefault(niche.lower(), []).append(acc.id)
            self._assignments[acc.id] = niche
            assigned.append(acc)
        return assigned

    def get_workload(self, niche: str = "") -> List[WorkloadInfo]:
        accounts = self._registry.get_active_accounts()
        if niche:
            accounts = [a for a in accounts if a.niche.lower() == niche.lower()]
        return sorted(
            [WorkloadInfo(a) for a in accounts],
            key=lambda w: w.utilization,
        )

    def get_least_loaded(self, platform: str = "", niche: str = "",
                         limit: int = 5) -> List[WorkloadInfo]:
        workload = self.get_workload(niche)
        if platform:
            workload = [w for w in workload if w.platform == platform]
        return [w for w in workload if w.available_slots > 0][:limit]

    def get_most_loaded(self, limit: int = 5) -> List[WorkloadInfo]:
        workload = self.get_workload()
        return sorted(workload, key=lambda w: w.utilization, reverse=True)[:limit]

    def get_workload_summary(self) -> Dict[str, Any]:
        accounts = self._registry.get_active_accounts()
        total_capacity = sum(a.daily_post_limit for a in accounts)
        total_used = sum(a.posts_today for a in accounts)
        return {
            "total_accounts": len(accounts),
            "total_capacity": total_capacity,
            "total_used": total_used,
            "overall_utilization": round(
                (total_used / total_capacity * 100) if total_capacity > 0 else 0, 1
            ),
            "available_slots": total_capacity - total_used,
            "by_platform": self._platform_workload(),
            "by_niche": self._niche_workload(),
        }

    def _platform_workload(self) -> Dict[str, Dict[str, int]]:
        result: Dict[str, Dict[str, int]] = {}
        for acc in self._registry.get_active_accounts():
            p = acc.platform
            if p not in result:
                result[p] = {"accounts": 0, "capacity": 0, "used": 0}
            result[p]["accounts"] += 1
            result[p]["capacity"] += acc.daily_post_limit
            result[p]["used"] += acc.posts_today
        return result

    def _niche_workload(self) -> Dict[str, Dict[str, int]]:
        result: Dict[str, Dict[str, int]] = {}
        for acc in self._registry.get_active_accounts():
            n = acc.niche or "unassigned"
            if n not in result:
                result[n] = {"accounts": 0, "capacity": 0, "used": 0}
            result[n]["accounts"] += 1
            result[n]["capacity"] += acc.daily_post_limit
            result[n]["used"] += acc.posts_today
        return result

    def get_assignment_status(self) -> Dict[str, Any]:
        return {
            "rules": len(self._rules),
            "assignments": len(self._assignments),
            "history": len(self._history),
            "workload": self.get_workload_summary(),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "rules": len(self._rules),
            "assignments": len(self._assignments),
            "history": len(self._history),
        }


def get_assignment_engine() -> AccountAssignmentEngine:
    return AccountAssignmentEngine()
