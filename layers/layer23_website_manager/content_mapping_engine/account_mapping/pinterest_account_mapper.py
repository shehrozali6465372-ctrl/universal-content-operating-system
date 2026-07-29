"""PinterestAccountMapper — Automatically choose the best Pinterest account for content."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.exceptions import AccountMappingError


class PinterestAccountMapper:
    """Map content to the best Pinterest business account by niche, audience, and performance."""

    # Predefined accounts by niche
    NICHE_ACCOUNTS: Dict[str, List[Dict[str, Any]]] = {
        "home_decor": [
            {"id": "acc_hd1", "name": "Modern Living Hub", "niche": "home_decor", "followers": 50000},
            {"id": "acc_hd2", "name": "Decor Inspo Daily", "niche": "home_decor", "followers": 35000},
        ],
        "fashion": [
            {"id": "acc_fa1", "name": "Style Vault", "niche": "fashion", "followers": 42000},
        ],
        "beauty": [
            {"id": "acc_be1", "name": "Beauty Bloom Studio", "niche": "beauty", "followers": 38000},
        ],
        "food": [
            {"id": "acc_fo1", "name": "Tasty Kitchen", "niche": "food", "followers": 55000},
        ],
        "tech": [
            {"id": "acc_te1", "name": "Tech Trends", "niche": "tech", "followers": 28000},
        ],
        "fitness": [
            {"id": "acc_fi1", "name": "Fit Life Daily", "niche": "fitness", "followers": 31000},
        ],
        "travel": [
            {"id": "acc_tr1", "name": "Wanderlust", "niche": "travel", "followers": 45000},
        ],
        "finance": [
            {"id": "acc_fn1", "name": "Money Smart", "niche": "finance", "followers": 22000},
        ],
        "diy": [
            {"id": "acc_di1", "name": "DIY Crafts Hub", "niche": "diy", "followers": 19000},
        ],
    }

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []

    def map_account(self, niche: str, preferred_account: str = "") -> Dict[str, Any]:
        """Map content to the best Pinterest account for the given niche."""
        accounts = self.NICHE_ACCOUNTS.get(niche, [])

        if not accounts:
            return {"id": "", "name": "", "confidence": 0.0}

        if preferred_account:
            for acc in accounts:
                if acc["id"] == preferred_account or acc["name"] == preferred_account:
                    result = {**acc, "confidence": 1.0}
                    self._mapping_log.append(result)
                    return result

        # Return the account with most followers
        best = max(accounts, key=lambda a: a["followers"])
        result = {**best, "confidence": 0.85}
        self._mapping_log.append(result)
        return result

    def get_available_accounts(self, niche: str) -> List[Dict[str, Any]]:
        return self.NICHE_ACCOUNTS.get(niche, [])

    def get_accounts_by_niche(self) -> Dict[str, List[Dict[str, Any]]]:
        return self.NICHE_ACCOUNTS

    def get_stats(self) -> Dict[str, Any]:
        return {"total_mappings": len(self._mapping_log)}
