"""embedding_validator.py — Embedding validation."""
from __future__ import annotations
from typing import Any, Dict, List


class EmbeddingValidator:
    """Validates embeddings for quality and consistency."""

    def __init__(self, expected_dimensions: int = 1536) -> None:
        self._expected = expected_dimensions

    def validate(self, vector: List[float]) -> List[str]:
        errors: List[str] = []
        if len(vector) != self._expected:
            errors.append(f"Dimension mismatch: {len(vector)} != {self._expected}")
        if not vector:
            errors.append("Empty vector")
        for i, v in enumerate(vector):
            if not isinstance(v, (int, float)):
                errors.append(f"Non-numeric at index {i}")
                break
        return errors

    def is_valid(self, vector: List[float]) -> bool:
        return len(self.validate(vector)) == 0

    def validate_batch(self, vectors: List[List[float]]) -> Dict[str, Any]:
        valid = sum(1 for v in vectors if self.is_valid(v))
        return {"total": len(vectors), "valid": valid,
                "invalid": len(vectors) - valid,
                "valid_rate": valid / max(1, len(vectors))}

    def fix(self, vector: List[float]) -> List[float]:
        if len(vector) < self._expected:
            return vector + [0.0] * (self._expected - len(vector))
        return vector[:self._expected]
