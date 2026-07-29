"""PinterestAccountMapper — Automatically select the best Pinterest account for content."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.exceptions import AccountMappingError


# Simulated Pinterest account registry
ACCOUNT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "pinterest_home": {
        "id": "pinterest_home",
        "name": "Modern Living Hub",
        "niche": "home_decor",
        "board_count": 8,
        "status": "active",
    },
    "pinterest_fashion": {
        "id": "pinterest_fashion",
        "name": "Style Vault",
        "niche": "fashion",
        "board_count": 6,
        "status": "active",
    },
    "pinterest_beauty": {
        "id": "pinterest_beauty",
        "name": "Beauty Bloom Studio",
        "niche": "beauty",
        "board_count": 5,
        "status": "active",
    },
    "pinterest_food": {
        "id": "pinterest_food",
        "name": "Tasty Kitchen",
        "niche": "food",
        "board_count": 7,
        "status": "active",
    },
    "pinterest_tech": {
        "id": "pinterest_tech",
        "name": "Gadget Flow",
        "niche": "tech",
        "board_count": 4,
        "status": "active",
    },
    "pinterest_fitness": {
        "id": "pinterest_fitness",
        "name": "Fit Life Hub",
        "niche": "fitness",
        "board_count": 5,
        "status": "active",
    },
    "pinterest_travel": {
        "id": "pinterest_travel",
        "name": "Wanderlust Diaries",
        "niche": "travel",
        "board_count": 6,
        "status": "active",
    },
    "pinterest_finance": {
        "id": "pinterest_finance",
        "name": "Wealth Wise",
        "niche": "finance",
        "board_count": 4,
        "status": "active",
    },
    "pinterest_diy": {
        "id": "pinterest_diy",
        "name": "DIY Crafts Master",
        "niche": "diy",
        "board_count": 6,
        "status": "active",
    },
    "pinterest_garden": {
        "id": "pinterest_garden",
        "name": "Garden Paradise",
        "niche": "garden",
        "board_count": 4,
        "status": "active",
    },
}


class PinterestAccountMapper:
    """Map content to the best Pinterest business account."""

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []
        self._total_mapped = 0

    def map_account(self, niche: str, topic: str = "") -> Dict[str, Any]:
        """Select the best Pinterest account for this content niche."""
        candidates = [a for a in ACCOUNT_REGISTRY.values()
                       if a["niche"] == niche and a["status"] == "active"]

        if not candidates:
            # Fallback to any active account
            candidates = [a for a in ACCOUNT_REGISTRY.values() if a["status"] == "active"]

        if not candidates:
            raise AccountMappingError(f"No active Pinterest account for niche: {niche}")

        account = candidates[0]
        result = {
            "account_id": account["id"],
            "account_name": account["name"],
            "niche": account["niche"],
            "board_count": account["board_count"],
            "confidence": 0.88,
        }

        self._mapping_log.append(result)
        self._total_mapped += 1
        return result

    def get_available_accounts(self) -> List[Dict[str, Any]]:
        return [a for a in ACCOUNT_REGISTRY.values() if a["status"] == "active"]

    def get_accounts_by_niche(self, niche: str) -> List[Dict[str, Any]]:
        return [a for a in ACCOUNT_REGISTRY.values()
                if a["niche"] == niche and a["status"] == "active"]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_mapped": self._total_mapped,
            "available_accounts": len([a for a in ACCOUNT_REGISTRY.values() if a["status"] == "active"]),
        }
