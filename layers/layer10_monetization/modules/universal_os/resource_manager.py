"""ResourceManager — bounded resource accounting."""
from __future__ import annotations
from typing import Any, Dict


class ResourceManager:
    """Track and manage system resources."""

    def __init__(self) -> None:
        self._resources: Dict[str, Dict[str, Any]] = {
            "cpu": {"allocated": 0.0, "used": 0.0, "limit": 100.0, "unit": "percent"},
            "ram": {"allocated": 0.0, "used": 0.0, "limit": 16384.0, "unit": "mb"},
            "gpu": {"allocated": 0.0, "used": 0.0, "limit": 100.0, "unit": "percent"},
            "storage": {"allocated": 0.0, "used": 0.0, "limit": 500000.0, "unit": "mb"},
            "bandwidth": {"allocated": 0.0, "used": 0.0, "limit": 1000.0, "unit": "gb"},
            "api_quota": {"allocated": 0.0, "used": 0.0, "limit": 10000.0, "unit": "requests"},
        }

    def allocate(self, resource_type: str, amount: float) -> bool:
        res = self._resources.get(resource_type)
        if res is None or amount < 0 or res["used"] + res["allocated"] + amount > res["limit"]:
            return False
        res["allocated"] += amount
        return True

    def release(self, resource_type: str, amount: float) -> bool:
        res = self._resources.get(resource_type)
        if res is None or amount < 0 or amount > res["allocated"]:
            return False
        res["allocated"] -= amount
        return True

    def use(self, resource_type: str, amount: float) -> bool:
        res = self._resources.get(resource_type)
        if res is None or amount < 0 or res["used"] + amount > res["limit"]:
            return False
        res["used"] += amount
        return True

    def get_available(self, resource_type: str) -> float:
        res = self._resources.get(resource_type)
        if res is None:
            return 0.0
        return max(0.0, res["limit"] - res["used"] - res["allocated"])

    def get_utilization(self, resource_type: str) -> float:
        res = self._resources.get(resource_type)
        if res is None or res["limit"] <= 0:
            return 0.0
        return round((res["used"] + res["allocated"]) / res["limit"], 4)

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: {**res, "available": self.get_available(name),
                   "utilization": self.get_utilization(name)}
            for name, res in self._resources.items()
        }

    def set_limit(self, resource_type: str, limit: float) -> None:
        if resource_type not in self._resources or limit <= 0:
            raise ValueError("resource type must exist and limit must be positive")
        res = self._resources[resource_type]
        if res["used"] + res["allocated"] > limit:
            raise ValueError("new limit is below current resource usage")
        res["limit"] = float(limit)

    def reset(self) -> None:
        for res in self._resources.values():
            res["allocated"] = 0.0
            res["used"] = 0.0

    def get_stats(self) -> Dict[str, Any]:
        return {name: {"used": r["used"], "allocated": r["allocated"],
                        "limit": r["limit"], "available": self.get_available(name),
                        "utilization": self.get_utilization(name)}
                for name, r in self._resources.items()}
