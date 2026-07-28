"""WebsiteClaimManager — Manage website claim status for Pinterest accounts."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_account_manager.exceptions import (
    WebsiteNotClaimedError,
)


class WebsiteClaimManager:
    """Manage Pinterest website claim — connection, verification, status."""

    CLAIM_STATUSES = ["not_claimed", "pending", "verified", "failed"]

    def __init__(self) -> None:
        self._claims: Dict[str, dict] = {}
        self._verification_log: List[dict] = []

    def claim_website(self, account_id: str, website: str) -> dict:
        """Initiate website claim for an account."""
        claim = {
            "account_id": account_id,
            "website": website,
            "claim_status": "pending",
            "verification_method": "html_meta_tag",
            "claimed_at": time.time(),
            "verified_at": 0.0,
        }
        self._claims[account_id] = claim
        self._verification_log.append({
            "action": "claim_initiated", "account_id": account_id,
            "website": website, "timestamp": time.time(),
        })
        return claim

    def verify_claim(self, account_id: str) -> dict:
        """Verify website claim (simulated: marks as verified)."""
        claim = self._claims.get(account_id)
        if not claim:
            raise WebsiteNotClaimedError(f"No claim found for account {account_id}")

        claim["claim_status"] = "verified"
        claim["verified_at"] = time.time()
        self._verification_log.append({
            "action": "claim_verified", "account_id": account_id,
            "timestamp": time.time(),
        })
        return claim

    def get_claim_status(self, account_id: str) -> str:
        """Get website claim status for an account."""
        claim = self._claims.get(account_id)
        return claim["claim_status"] if claim else "not_claimed"

    def is_claimed(self, account_id: str) -> bool:
        """Check if website is claimed and verified."""
        return self.get_claim_status(account_id) == "verified"

    def remove_claim(self, account_id: str) -> bool:
        """Remove website claim."""
        return self._claims.pop(account_id, None) is not None

    def get_stats(self) -> Dict[str, Any]:
        by_status: Dict[str, int] = {}
        for claim in self._claims.values():
            s = claim["claim_status"]
            by_status[s] = by_status.get(s, 0) + 1
        return {
            "total_claims": len(self._claims),
            "by_status": by_status,
            "verified": sum(1 for c in self._claims.values() if c["claim_status"] == "verified"),
            "total_attempts": len(self._verification_log),
        }
