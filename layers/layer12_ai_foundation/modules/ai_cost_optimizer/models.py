"""Data models for AI Cost Optimizer."""
from __future__ import annotations
import uuid
import time
from typing import Any, Dict
from dataclasses import dataclass, field

@dataclass
class CostEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    provider: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens
    def to_dict(self) -> Dict[str, Any]:
        return {"entry_id": self.entry_id, "provider": self.provider, "model": self.model,
                "prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens,
                "cost_usd": round(self.cost_usd, 6)}

@dataclass
class BudgetLimit:
    daily: float = 10.0
    weekly: float = 50.0
    monthly: float = 200.0
    alert_threshold: float = 0.8
    hard_stop: bool = True
    def to_dict(self) -> Dict[str, Any]:
        return {"daily": self.daily, "weekly": self.weekly, "monthly": self.monthly}
