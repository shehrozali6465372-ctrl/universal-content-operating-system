"""Data models for AI Reasoning Engine."""
from __future__ import annotations

import uuid
import time
from typing import Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum


class ReasoningType(str, Enum):
    LOGICAL = "logical"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    STRATEGIC = "strategic"
    MATHEMATICAL = "mathematical"
    PLANNING = "planning"
    REFLECTION = "reflection"
    SELF_CRITIQUE = "self_critique"
    VERIFICATION = "verification"
    DECISION = "decision"


@dataclass
class ReasoningStep:
    """Single step in a reasoning chain."""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    step_type: str = "thought"
    content: str = ""
    confidence: float = 0.5
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"step_id": self.step_id, "type": self.step_type,
                "content": self.content[:200], "confidence": self.confidence,
                "evidence": self.evidence}


@dataclass
class ReasoningChain:
    """Chain of reasoning steps leading to a conclusion."""
    chain_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    reasoning_type: ReasoningType = ReasoningType.LOGICAL
    steps: List[ReasoningStep] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.0
    is_valid: bool = True
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def add_step(self, step: ReasoningStep) -> None:
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id, "type": self.reasoning_type.value,
            "step_count": self.step_count, "conclusion": self.conclusion[:200],
            "confidence": self.confidence, "is_valid": self.is_valid,
        }


@dataclass
class ReasoningResult:
    """Result of a reasoning operation."""
    chain: ReasoningChain = field(default_factory=ReasoningChain)
    answer: str = ""
    confidence: float = 0.0
    alternatives: List[str] = field(default_factory=list)
    reasoning_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer[:200], "confidence": self.confidence,
            "alternatives": [a[:100] for a in self.alternatives],
            "reasoning_time_ms": round(self.reasoning_time_ms, 2),
            "chain_steps": self.chain.step_count,
        }
