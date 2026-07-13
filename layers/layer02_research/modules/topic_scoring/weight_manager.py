"""
Weight Manager
Layer 2: Research Engine — Module 8

Niche-specific scoring weight management:
- Default weights
- Niche-specific overrides
- Weight validation
- Weight interpolation
"""

from typing import Dict, List


# Default scoring dimensions
SCORING_DIMENSIONS = [
    "trend", "audience", "competition", "knowledge",
    "verification", "engagement", "freshness",
]

# Default weights (must sum to 1.0)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "trend": 0.20,
    "audience": 0.25,
    "competition": 0.15,
    "knowledge": 0.15,
    "verification": 0.15,
    "engagement": 0.05,
    "freshness": 0.05,
}

# Niche-specific weight overrides
NICHE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "finance": {
        "trend": 0.20, "audience": 0.20, "competition": 0.15,
        "knowledge": 0.15, "verification": 0.25, "engagement": 0.03, "freshness": 0.02,
    },
    "technology": {
        "trend": 0.25, "audience": 0.20, "competition": 0.10,
        "knowledge": 0.20, "verification": 0.15, "engagement": 0.05, "freshness": 0.05,
    },
    "health": {
        "trend": 0.15, "audience": 0.25, "competition": 0.10,
        "knowledge": 0.15, "verification": 0.25, "engagement": 0.05, "freshness": 0.05,
    },
    "education": {
        "trend": 0.15, "audience": 0.25, "competition": 0.10,
        "knowledge": 0.20, "verification": 0.20, "engagement": 0.05, "freshness": 0.05,
    },
    "entertainment": {
        "trend": 0.30, "audience": 0.25, "competition": 0.15,
        "knowledge": 0.10, "verification": 0.05, "engagement": 0.10, "freshness": 0.05,
    },
    "business": {
        "trend": 0.20, "audience": 0.25, "competition": 0.20,
        "knowledge": 0.15, "verification": 0.10, "engagement": 0.05, "freshness": 0.05,
    },
    "ai": {
        "trend": 0.25, "audience": 0.20, "competition": 0.10,
        "knowledge": 0.20, "verification": 0.15, "engagement": 0.05, "freshness": 0.05,
    },
    "crypto": {
        "trend": 0.35, "audience": 0.15, "competition": 0.15,
        "knowledge": 0.10, "verification": 0.15, "engagement": 0.05, "freshness": 0.05,
    },
    "fitness": {
        "trend": 0.15, "audience": 0.30, "competition": 0.15,
        "knowledge": 0.15, "verification": 0.10, "engagement": 0.10, "freshness": 0.05,
    },
    "cooking": {
        "trend": 0.15, "audience": 0.25, "competition": 0.20,
        "knowledge": 0.15, "verification": 0.05, "engagement": 0.10, "freshness": 0.10,
    },
    "travel": {
        "trend": 0.20, "audience": 0.25, "competition": 0.20,
        "knowledge": 0.10, "verification": 0.05, "engagement": 0.10, "freshness": 0.10,
    },
    "parenting": {
        "trend": 0.10, "audience": 0.30, "competition": 0.15,
        "knowledge": 0.20, "verification": 0.15, "engagement": 0.05, "freshness": 0.05,
    },
    "motivation": {
        "trend": 0.15, "audience": 0.30, "competition": 0.15,
        "knowledge": 0.10, "verification": 0.10, "engagement": 0.10, "freshness": 0.10,
    },
}


class WeightManager:
    """Manage scoring weights by niche."""

    def __init__(self):
        self._overrides: Dict[str, Dict[str, float]] = dict(NICHE_WEIGHTS)

    def get_weights(self, niche: str = "general") -> Dict[str, float]:
        """Get weights for a specific niche."""
        return dict(self._overrides.get(niche, DEFAULT_WEIGHTS))

    def set_weights(self, niche: str, weights: Dict[str, float]):
        """Override weights for a niche."""
        # Validate
        total = sum(weights.values())
        if abs(total - 1.0) > 0.05:
            raise ValueError(f"Weights must sum to ~1.0, got {total:.3f}")
        for dim in weights:
            if dim not in SCORING_DIMENSIONS:
                raise ValueError(f"Unknown dimension: {dim}")
        self._overrides[niche] = dict(weights)

    def get_all_niches(self) -> List[str]:
        return sorted(self._overrides.keys())

    def interpolate(self, niche_a: str, niche_b: str, ratio: float = 0.5) -> Dict[str, float]:
        """Interpolate weights between two niches."""
        wa = self.get_weights(niche_a)
        wb = self.get_weights(niche_b)
        ratio = max(0.0, min(1.0, ratio))
        return {
            dim: round(wa.get(dim, 0) * (1 - ratio) + wb.get(dim, 0) * ratio, 4)
            for dim in SCORING_DIMENSIONS
        }

    def register_niche(self, niche: str, weights: Dict[str, float]):
        """Register a new niche with weights."""
        self.set_weights(niche, weights)

    def remove_niche(self, niche: str) -> bool:
        if niche in self._overrides:
            del self._overrides[niche]
            return True
        return False

    def normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normalize weights to sum to 1.0."""
        total = sum(weights.values())
        if total == 0:
            return dict(DEFAULT_WEIGHTS)
        return {k: round(v / total, 4) for k, v in weights.items()}
