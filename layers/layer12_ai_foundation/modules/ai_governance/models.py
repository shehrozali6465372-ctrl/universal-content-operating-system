"""Data models for AI Governance."""
from __future__ import annotations
import uuid
import time
from typing import Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum

class PolicyType(str, Enum):
    ETHICS = "ethics"; COPYRIGHT = "copyright"; PRIVACY = "privacy"; SAFETY = "safety"
    CONTENT = "content"; PLATFORM = "platform"; BRAND = "brand"

@dataclass
class Policy:
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""; policy_type: PolicyType = PolicyType.ETHICS
    rules: List[str] = field(default_factory=list)
    severity: str = "medium"
    active: bool = True
    created_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict[str, Any]:
        return {"policy_id": self.policy_id, "name": self.name, "type": self.policy_type.value,
                "rules": self.rules, "severity": self.severity, "active": self.active}

@dataclass
class Violation:
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    policy_id: str = ""; policy_type: str = ""; severity: str = "medium"
    description: str = ""; content_preview: str = ""
    timestamp: float = field(default_factory=time.time)
    def to_dict(self) -> Dict[str, Any]:
        return {"violation_id": self.violation_id, "policy_id": self.policy_id,
                "type": self.policy_type, "severity": self.severity,
                "description": self.description[:200]}
