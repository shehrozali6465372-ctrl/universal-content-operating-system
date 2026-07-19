"""GovernanceConfig — configuration for governance system."""
from __future__ import annotations
from typing import Any, Dict

class GovernanceConfig:
    def __init__(self, **kwargs: Any) -> None:
        self.enforce_copyright: bool = kwargs.get("enforce_copyright", True)
        self.enforce_privacy: bool = kwargs.get("enforce_privacy", True)
        self.enforce_safety: bool = kwargs.get("enforce_safety", True)
        self.enforce_ethics: bool = kwargs.get("enforce_ethics", True)
        self.block_on_critical: bool = kwargs.get("block_on_critical", True)
        self.max_violations_before_block: int = kwargs.get("max_violations_before_block", 5)
        self.log_all_violations: bool = kwargs.get("log_all_violations", True)
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
