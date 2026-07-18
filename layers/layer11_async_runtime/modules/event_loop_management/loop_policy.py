"""LoopPolicy — Configure loop scheduling policies."""
from __future__ import annotations
from typing import Any, Dict

class LoopPolicy:
    def __init__(self) -> None:
        self.policies: Dict[str, Any] = {"default": {"priority": 1, "max_tasks": 100}}
    def set_policy(self, name: str, config: Dict[str, Any]) -> None:
        self.policies[name] = config
    def get_policy(self, name: str) -> Dict[str, Any]:
        return self.policies.get(name, self.policies["default"])
    def get_all(self) -> Dict[str, Any]:
        return dict(self.policies)
    def get_stats(self) -> Dict[str, Any]:
        return {"total_policies": len(self.policies)}
