"""Data models for Multi Model Intelligence."""
from __future__ import annotations

import uuid
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ModelResponse:
    """Response from a single model."""
    model: str
    provider: str
    content: str
    score: float = 0.0
    confidence: float = 0.0
    latency_ms: float = 0.0
    tokens_used: int = 0
    response_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.error is None and bool(self.content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model, "provider": self.provider,
            "content": self.content, "score": self.score,
            "confidence": self.confidence, "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used, "response_id": self.response_id,
            "metadata": self.metadata, "error": self.error,
        }


@dataclass
class VoteResult:
    """Result of a voting round."""
    candidate: str
    votes: int
    voters: List[str] = field(default_factory=list)
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {"candidate": self.candidate, "votes": self.votes,
                "voters": self.voters, "weight": self.weight}


@dataclass
class RankEntry:
    """Ranked item."""
    rank: int
    response: Optional[ModelResponse] = None
    score: float = 0.0
    breakdown: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"rank": self.rank, "score": self.score,
                "model": self.response.model if self.response else "",
                "breakdown": self.breakdown}


@dataclass
class ConsensusResult:
    """Consensus outcome."""
    agreed_content: str
    agreement_score: float
    participating_models: int
    method: str = "majority"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"agreed_content": self.agreed_content,
                "agreement_score": self.agreement_score,
                "participating_models": self.participating_models,
                "method": self.method, "details": self.details}
