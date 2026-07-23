"""ScalingEngine — Scales from 60 to 10,000+ accounts without code changes."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class ScalingTier:
    __slots__ = ("name", "min_accounts", "max_accounts", "recommended_workers",
                 "recommended_db_pool", "recommended_cache_size",
                 "recommended_batch_size", "config_overrides")

    def __init__(self, name: str, min_accounts: int, max_accounts: int,
                 workers: int = 1, db_pool: int = 10,
                 cache_size: int = 1000, batch_size: int = 50) -> None:
        self.name = name
        self.min_accounts = min_accounts
        self.max_accounts = max_accounts
        self.recommended_workers = workers
        self.recommended_db_pool = db_pool
        self.recommended_cache_size = cache_size
        self.recommended_batch_size = batch_size
        self.config_overrides: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "accounts": f"{self.min_accounts}-{self.max_accounts}",
            "workers": self.recommended_workers,
            "db_pool": self.recommended_db_pool,
            "cache_mb": self.recommended_cache_size,
            "batch_size": self.recommended_batch_size,
        }


class ScalingPlan:
    __slots__ = ("id", "current_tier", "target_tier", "current_accounts",
                 "target_accounts", "estimated_cost", "steps", "status", "created_at")

    def __init__(self, current_tier: str, target_tier: str,
                 current_accounts: int, target_accounts: int) -> None:
        self.id = f"plan_{int(time.time() * 1000)}"
        self.current_tier = current_tier
        self.target_tier = target_tier
        self.current_accounts = current_accounts
        self.target_accounts = target_accounts
        self.estimated_cost = 0.0
        self.steps: List[str] = []
        self.status = "planned"
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "from": self.current_tier, "to": self.target_tier,
            "current": self.current_accounts, "target": self.target_accounts,
            "cost": round(self.estimated_cost, 2),
            "steps": self.steps, "status": self.status,
        }


class ScalingEngine:
    """Manages scaling from small to enterprise with zero code changes."""
    _instance: Optional["ScalingEngine"] = None
    _lock = threading.Lock()

    TIERS = [
        ScalingTier("starter", 0, 100, workers=1, db_pool=10, cache_size=256, batch_size=25),
        ScalingTier("growth", 100, 500, workers=3, db_pool=20, cache_size=512, batch_size=50),
        ScalingTier("scale", 500, 2000, workers=5, db_pool=30, cache_size=1024, batch_size=100),
        ScalingTier("enterprise", 2000, 10000, workers=10, db_pool=50, cache_size=2048, batch_size=200),
        ScalingTier("empire", 10000, 100000, workers=20, db_pool=100, cache_size=4096, batch_size=500),
    ]

    def __new__(cls) -> "ScalingEngine":
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
        self._tiers: Dict[str, ScalingTier] = {}
        self._plans: Dict[str, ScalingPlan] = {}
        self._current_accounts = 0
        self._scaling_history: List[Dict[str, Any]] = []
        for tier in self.TIERS:
            self._tiers[tier.name] = tier

    def get_tier(self, account_count: int) -> ScalingTier:
        for tier in self.TIERS:
            if tier.min_accounts <= account_count < tier.max_accounts:
                return tier
        return self.TIERS[-1]

    def get_current_tier(self) -> ScalingTier:
        return self.get_tier(self._current_accounts)

    def set_account_count(self, count: int) -> None:
        old_tier = self.get_current_tier()
        self._current_accounts = count
        new_tier = self.get_current_tier()
        if old_tier.name != new_tier.name:
            self._scaling_history.append({
                "from_tier": old_tier.name, "to_tier": new_tier.name,
                "accounts": count, "timestamp": time.time(),
            })

    def create_scaling_plan(self, target_accounts: int) -> ScalingPlan:
        current_tier = self.get_current_tier()
        target_tier = self.get_tier(target_accounts)
        plan = ScalingPlan(
            current_tier.name, target_tier.name,
            self._current_accounts, target_accounts,
        )
        plan.steps = self._generate_steps(current_tier, target_tier, target_accounts)
        plan.estimated_cost = self._estimate_cost(target_tier)
        plan.status = "ready"
        self._plans[plan.id] = plan
        return plan

    def _generate_steps(self, current: ScalingTier, target: ScalingTier,
                        target_accounts: int) -> List[str]:
        steps = []
        if target.recommended_workers > current.recommended_workers:
            steps.append(f"Increase workers: {current.recommended_workers} → {target.recommended_workers}")
        if target.recommended_db_pool > current.recommended_db_pool:
            steps.append(f"Increase DB pool: {current.recommended_db_pool} → {target.recommended_db_pool}")
        if target.recommended_cache_size > current.recommended_cache_size:
            steps.append(f"Increase cache: {current.recommended_cache_size}MB → {target.recommended_cache_size}MB")
        if target.recommended_batch_size > current.recommended_batch_size:
            steps.append(f"Increase batch size: {current.recommended_batch_size} → {target.recommended_batch_size}")
        steps.append(f"Register {target_accounts} accounts in registry")
        steps.append("No code changes required — architecture is scalable")
        return steps

    def _estimate_cost(self, tier: ScalingTier) -> float:
        base_costs = {
            "starter": 0, "growth": 50, "scale": 200,
            "enterprise": 800, "empire": 3000,
        }
        return base_costs.get(tier.name, 0)

    def get_scaling_status(self) -> Dict[str, Any]:
        current = self.get_current_tier()
        return {
            "current_accounts": self._current_accounts,
            "current_tier": current.to_dict(),
            "all_tiers": [t.to_dict() for t in self.TIERS],
            "active_plans": sum(1 for p in self._plans.values() if p.status == "ready"),
            "scaling_events": len(self._scaling_history),
            "next_tier": self.TIERS[self.TIERS.index(current) + 1].to_dict()
            if self.TIERS.index(current) < len(self.TIERS) - 1 else None,
        }

    def get_recommendations(self) -> List[str]:
        recs = []
        current = self.get_current_tier()
        idx = self.TIERS.index(current)
        if idx < len(self.TIERS) - 1:
            next_tier = self.TIERS[idx + 1]
            remaining = next_tier.min_accounts - self._current_accounts
            if remaining < 50:
                recs.append(f"Next tier ({next_tier.name}) in {remaining} accounts")
            recs.append(f"Current config: {current.recommended_workers} workers, "
                       f"{current.recommended_db_pool} DB connections")
        else:
            recs.append("Maximum tier reached — consider infrastructure optimization")
        return recs

    def stats(self) -> Dict[str, Any]:
        return {
            "tiers": len(self._tiers),
            "plans": len(self._plans),
            "current_accounts": self._current_accounts,
            "history": len(self._scaling_history),
        }


def get_scaling_engine() -> ScalingEngine:
    return ScalingEngine()
