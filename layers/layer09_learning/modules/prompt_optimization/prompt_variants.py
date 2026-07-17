"""Prompt Variants — Create and manage prompt variants for A/B testing."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.prompt_optimization.prompt_profile import PromptProfile


class PromptVariant:
    """A variant of a prompt for A/B testing."""

    __slots__ = ("variant_id", "variant_label", "profile", "weight",
                 "is_control", "created_at", "performance_data")

    _counter = 0

    def __init__(self, profile: PromptProfile, variant_label: str = "B",
                 is_control: bool = False) -> None:
        PromptVariant._counter += 1
        self.variant_id: str = f"pv_{PromptVariant._counter}"
        self.variant_label = variant_label
        self.profile = profile
        self.weight: float = 1.0
        self.is_control = is_control
        self.created_at: float = time.time()
        self.performance_data: Dict[str, Any] = {}

    @property
    def effective_score(self) -> float:
        return self.profile.effective_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "variant_label": self.variant_label,
            "profile_id": self.profile.profile_id,
            "is_control": self.is_control,
            "weight": self.weight,
            "effective_score": self.effective_score,
        }


class VariantTest:
    """An A/B test comparing prompt variants."""

    __slots__ = ("test_id", "test_name", "variants", "status",
                 "created_at", "completed_at", "winner_id", "min_samples")

    _counter = 0

    def __init__(self, test_name: str = "", min_samples: int = 10) -> None:
        VariantTest._counter += 1
        self.test_id: str = f"vt_{VariantTest._counter}"
        self.test_name = test_name
        self.variants: List[PromptVariant] = []
        self.status: str = "running"
        self.created_at: float = time.time()
        self.completed_at: Optional[float] = None
        self.winner_id: Optional[str] = None
        self.min_samples = min_samples

    def add_variant(self, variant: PromptVariant) -> None:
        self.variants.append(variant)

    def get_control(self) -> Optional[PromptVariant]:
        for v in self.variants:
            if v.is_control:
                return v
        return None

    def get_winner(self) -> Optional[PromptVariant]:
        if self.winner_id:
            for v in self.variants:
                if v.variant_id == self.winner_id:
                    return v
        return None

    def has_sufficient_samples(self) -> bool:
        return all(v.profile.usage_count >= self.min_samples for v in self.variants)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "variant_count": len(self.variants),
            "status": self.status,
            "winner_id": self.winner_id,
            "has_sufficient_samples": self.has_sufficient_samples(),
        }


class PromptVariants:
    """Manage prompt variants and A/B tests."""

    def __init__(self) -> None:
        self._tests: List[VariantTest] = []
        self._active_variants: Dict[str, List[PromptVariant]] = {}

    def create_test(self, name: str, baseline: PromptProfile,
                    candidates: List[PromptProfile], min_samples: int = 10) -> VariantTest:
        test = VariantTest(name, min_samples)
        control = PromptVariant(baseline, "A", is_control=True)
        test.add_variant(control)
        for i, candidate in enumerate(candidates):
            label = chr(ord("B") + i)
            variant = PromptVariant(candidate, label)
            test.add_variant(variant)
        self._tests.append(test)
        return test

    def record_outcome(self, test_id: str, variant_id: str, success: bool,
                       engagement: float = 0.0, quality: float = 0.0) -> None:
        test = self.get_test(test_id)
        if not test:
            return
        for v in test.variants:
            if v.variant_id == variant_id:
                v.profile.record_usage(success, engagement, quality)
                break

    def evaluate_test(self, test_id: str) -> Optional[str]:
        test = self.get_test(test_id)
        if not test or not test.has_sufficient_samples():
            return None
        best = max(test.variants, key=lambda v: v.effective_score)
        test.winner_id = best.variant_id
        test.status = "completed"
        test.completed_at = time.time()
        return best.variant_id

    def get_test(self, test_id: str) -> Optional[VariantTest]:
        for t in self._tests:
            if t.test_id == test_id:
                return t
        return None

    def get_tests(self, status: str = "") -> List[VariantTest]:
        if status:
            return [t for t in self._tests if t.status == status]
        return list(self._tests)

    @property
    def test_count(self) -> int:
        return len(self._tests)
