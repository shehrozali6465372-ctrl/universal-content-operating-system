"""Data models for AI Evaluation Engine."""
from __future__ import annotations
import uuid
import time
from typing import Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum

class EvalType(str, Enum):
    QUALITY = "quality"; ACCURACY = "accuracy"; HALLUCINATION = "hallucination"
    BIAS = "bias"; SAFETY = "safety"; GRAMMAR = "grammar"; SEO = "seo"
    CREATIVITY = "creativity"; CONSISTENCY = "consistency"; BRAND_VOICE = "brand_voice"

@dataclass
class EvalResult:
    result_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    eval_type: EvalType = EvalType.QUALITY
    score: float = 0.0
    passed: bool = True
    details: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    def to_dict(self) -> Dict[str, Any]:
        return {"result_id": self.result_id, "type": self.eval_type.value,
                "score": round(self.score, 4), "passed": self.passed, "issues": self.issues}

@dataclass
class EvalCriteria:
    name: str = ""
    weight: float = 1.0
    threshold: float = 0.5
    description: str = ""
