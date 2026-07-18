"""persistence_capabilities.py — Persistence capabilities."""
from __future__ import annotations
from typing import Any, Dict, List


class PersistenceCapabilities:
    """Tracks available persistence capabilities."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str = "",
                 features: List[str] = None) -> None:
        self._capabilities[name] = {"description": description,
                                      "features": features or [],
                                      "enabled": True}

    def has(self, name: str) -> bool:
        cap = self._capabilities.get(name)
        return cap is not None and cap.get("enabled", False)

    def enable(self, name: str) -> None:
        if name in self._capabilities:
            self._capabilities[name]["enabled"] = True

    def disable(self, name: str) -> None:
        if name in self._capabilities:
            self._capabilities[name]["enabled"] = False

    def get_features(self, name: str) -> List[str]:
        cap = self._capabilities.get(name)
        return cap["features"] if cap else []

    def list_all(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._capabilities)

    def enabled_count(self) -> int:
        return sum(1 for c in self._capabilities.values() if c.get("enabled"))

    def stats(self) -> Dict[str, Any]:
        return {"total": len(self._capabilities), "enabled": self.enabled_count()}
