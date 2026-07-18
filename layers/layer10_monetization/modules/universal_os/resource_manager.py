"""ResourceManager — Manage CPU, RAM, GPU, API quotas, storage, bandwidth."""
from __future__ import annotations
from typing import Any, Dict


class ResourceManager:
    """Track and manage system resources."""

    def __init__(self) -> None:
        self._resources: Dict[str, Dict[str, Any]] = {
            "cpu": {"allocated": 0, "used": 0, "limit": 100, "unit": "percent"},
            "ram": {"allocated": 0, "used": 0, "limit": 16384, "unit": "mb"},
            "gpu": {"allocated": 0, "used": 0, "limit": 100, "unit": "percent"},
            "storage": {"allocated": 0, "used": 0, "limit": 500000, "unit": "mb"},
            "bandwidth": {"allocated": 0, "used": 0, "limit": 1000, "unit": "gb"},
            "api_quota": {"allocated": 0, "used": 0, "limit": 10000, "unit": "requests"},
        }

    def allocate(self, resource_type: str, amount: float) -> bool:
        res = self._resources.get(resource_type)
        if res is None or amount < 0:
            return False
        if res["allocated"] + amount <= res["limit"]:
            res["allocated"] += amount
            return True
        return False

    def release(self, resource_type: str, amount: float) -> bool:
        res = self._resources.get(resource_type)
        if res is None:
            return False
        res["allocated"] = max(0, res["allocated"] - amount)
        return True

    def use(self, resource_type: str, amount: float) -> bool:
        res = self._resources.get(resource_type)
        if res is None:
            return False
        if res["used"] + amount <= res["limit"]:
            res["used"] += amount
            return True
        return False

    def get_available(self, resource_type: str) -> float:
        res = self._resources.get(resource_type)
        if res is None:
            return 0.0
        return res["limit"] - res["used"]

    def get_utilization(self, resource_type: str) -> float:
        res = self._resources.get(resource_type)
        if res is None or res["limit"] == 0:
            return 0.0
        return round(res["used"] / res["limit"], 4)

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for name, res in self._resources.items():
            result[name] = {**res, "available": res["limit"] - res["used"],
                            "utilization": round(res["used"] / max(1, res["limit"]), 4)}
        return result

    def set_limit(self, resource_type: str, limit: float) -> None:
        if resource_type in self._resources:
            self._resources[resource_type]["limit"] = limit

    def reset(self) -> None:
        for res in self._resources.values():
            res["allocated"] = 0
            res["used"] = 0

    def get_stats(self) -> Dict[str, Any]:
        return {name: {"used": r["used"], "limit": r["limit"],
                        "utilization": round(r["used"] / max(1, r["limit"]), 4)}
                for name, r in self._resources.items()}
