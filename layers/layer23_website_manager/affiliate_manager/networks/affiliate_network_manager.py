"""AffiliateNetworkManager — Manage affiliate networks: Amazon, Impact, CJ, ShareASale, etc."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.models.affiliate_models import (
    AffiliateNetwork, NetworkStatus,
)
from layers.layer23_website_manager.affiliate_manager.exceptions import AffiliateNetworkError


class AffiliateNetworkManager:
    """Register, configure, and manage affiliate networks."""

    PRESET_NETWORKS = [
        {"name": "Amazon Associates", "country": "US", "commission": 6.0, "cookie_days": 1, "min_payout": 10.0},
        {"name": "Impact", "country": "US", "commission": 8.0, "cookie_days": 30, "min_payout": 50.0},
        {"name": "CJ Affiliate", "country": "US", "commission": 7.0, "cookie_days": 30, "min_payout": 50.0},
        {"name": "ShareASale", "country": "US", "commission": 6.0, "cookie_days": 30, "min_payout": 50.0},
        {"name": "Awin", "country": "US", "commission": 7.0, "cookie_days": 30, "min_payout": 20.0},
        {"name": "Rakuten", "country": "US", "commission": 5.0, "cookie_days": 30, "min_payout": 50.0},
        {"name": "ClickBank", "country": "US", "commission": 50.0, "cookie_days": 60, "min_payout": 10.0},
        {"name": "Digistore24", "country": "US", "commission": 40.0, "cookie_days": 60, "min_payout": 20.0},
    ]

    def __init__(self) -> None:
        self._networks: Dict[str, AffiliateNetwork] = {}
        self._lock = threading.Lock()

    def register_network(self, network_name: str, country: str = "US",
                          api_key: str = "", commission_rate: float = 0.0,
                          cookie_days: int = 30) -> AffiliateNetwork:
        """Register a new affiliate network."""
        network = AffiliateNetwork(
            network_name=network_name,
            api_key=api_key,
            country=country,
            commission_rate=commission_rate,
            cookie_days=cookie_days,
            status=NetworkStatus.PENDING,
        )
        with self._lock:
            self._networks[network.network_id] = network
        return network

    def load_presets(self) -> List[AffiliateNetwork]:
        """Load preset affiliate networks."""
        networks = []
        for preset in self.PRESET_NETWORKS:
            net = self.register_network(
                network_name=preset["name"],
                country=preset["country"],
                commission_rate=preset["commission"],
                cookie_days=preset["cookie_days"],
            )
            net.min_payout = preset["min_payout"]
            networks.append(net)
        return networks

    def get_network(self, network_id: str) -> Optional[AffiliateNetwork]:
        return self._networks.get(network_id)

    def get_all_networks(self, status: Optional[NetworkStatus] = None) -> List[AffiliateNetwork]:
        nets = list(self._networks.values())
        if status:
            nets = [n for n in nets if n.status == status]
        return nets

    def activate_network(self, network_id: str) -> bool:
        net = self._networks.get(network_id)
        if not net:
            return False
        net.status = NetworkStatus.ACTIVE
        net.updated_at = time.time()
        return True

    def deactivate_network(self, network_id: str) -> bool:
        net = self._networks.get(network_id)
        if not net:
            return False
        net.status = NetworkStatus.INACTIVE
        net.updated_at = time.time()
        return True

    def delete_network(self, network_id: str) -> bool:
        return self._networks.pop(network_id, None) is not None

    def get_stats(self) -> Dict[str, Any]:
        by_status: Dict[str, int] = {}
        for n in self._networks.values():
            by_status[n.status.value] = by_status.get(n.status.value, 0) + 1
        return {
            "total_networks": len(self._networks),
            "by_status": by_status,
            "total_earnings": sum(n.total_earnings for n in self._networks.values()),
        }
