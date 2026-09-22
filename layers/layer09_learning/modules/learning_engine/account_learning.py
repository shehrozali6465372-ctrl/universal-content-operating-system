"""Persistent account-local learning feedback store."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore


class AccountLearningStore:
    """Persist outcomes per account so one niche cannot train another account's state."""

    def __init__(self, store: AccountDataStore | None = None) -> None:
        self.store = store or AccountDataStore()

    def record(self, account_id: str, *, platform: str, niche: str, topic: str,
               quality_score: float, published: bool, analytics: Any = None,
               content_type: str = "post", policy_version: str | None = None) -> Dict[str, Any]:
        event = {
            "timestamp": time.time(), "account_id": account_id, "platform": platform,
            "niche": niche, "topic": topic, "quality_score": float(quality_score),
            "published": bool(published), "analytics": analytics if analytics is not None else "UNKNOWN",
            "observed": analytics is not None,
            "content_type": content_type, "policy_version": policy_version,
        }
        self.store.append(account_id, "learning", "execution_outcomes", event)
        return event

    def recent(self, account_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        values = self.store.get(account_id, "learning", "collection:execution_outcomes", [])
        return values[-limit:]

    def performance_summary(self, account_id: str) -> Dict[str, Any]:
        values = self.recent(account_id, 1000)
        observed = [v for v in values if bool(v.get("observed")) and v.get("analytics") != "UNKNOWN"]
        if not observed:
            return {
                "account_id": account_id,
                "observations": 0,
                "quality_average": None,
                "published_rate": None,
                "analytics_known": 0,
            }
        return {
            "account_id": account_id,
            "observations": len(observed),
            "quality_average": sum(v["quality_score"] for v in observed) / len(observed),
            "published_rate": sum(1 for v in observed if v["published"]) / len(observed),
            "analytics_known": len(observed),
        }
