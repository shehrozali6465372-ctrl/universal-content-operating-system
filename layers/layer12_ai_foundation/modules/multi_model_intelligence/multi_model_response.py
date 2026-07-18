"""MultiModelResponse — aggregate response from multi-model operation."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .models import ModelResponse


class MultiModelResponse:
    """Aggregate response from multi-model operations."""

    def __init__(self) -> None:
        self.responses: List[ModelResponse] = []
        self.best: Optional[ModelResponse] = None
        self.consensus_score: float = 0.0
        self.confidence: float = 0.0
        self.method: str = ""
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()

    def add_response(self, response: ModelResponse) -> None:
        self.responses.append(response)

    def set_best(self, response: ModelResponse) -> None:
        self.best = response

    @property
    def successful_count(self) -> int:
        return sum(1 for r in self.responses if r.is_success)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.responses if not r.is_success)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "best_model": self.best.model if self.best else None,
            "best_content": self.best.content if self.best else None,
            "consensus_score": self.consensus_score,
            "confidence": self.confidence,
            "method": self.method,
            "total_responses": len(self.responses),
            "successful": self.successful_count,
            "failed": self.failed_count,
        }
