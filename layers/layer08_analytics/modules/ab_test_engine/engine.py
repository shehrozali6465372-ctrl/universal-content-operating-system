"""A/B Test Engine — Run, analyze, and determine winners of A/B tests."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class ABVariant:
    """A variant in an A/B test."""

    __slots__ = ("variant_id", "name", "impressions", "conversions",
                 "revenue", "metadata")

    def __init__(self, variant_id: str = "", name: str = "") -> None:
        self.variant_id = variant_id
        self.name = name
        self.impressions: int = 0
        self.conversions: int = 0
        self.revenue: float = 0.0
        self.metadata: Dict[str, Any] = {}

    @property
    def conversion_rate(self) -> float:
        return (self.conversions / max(1, self.impressions)) * 100

    @property
    def revenue_per_impression(self) -> float:
        return self.revenue / max(1, self.impressions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "name": self.name,
            "impressions": self.impressions,
            "conversions": self.conversions,
            "conversion_rate": round(self.conversion_rate, 3),
            "revenue": round(self.revenue, 2),
        }


class ABTest:
    """An A/B test experiment."""

    __slots__ = ("test_id", "name", "variants", "status",
                 "started_at", "ended_at", "winner", "metadata")

    def __init__(self, test_id: str = "", name: str = "") -> None:
        self.test_id = test_id
        self.name = name
        self.variants: List[ABVariant] = []
        self.status: str = "draft"
        self.started_at: float = 0.0
        self.ended_at: float = 0.0
        self.winner: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def add_variant(self, variant: ABVariant) -> None:
        self.variants.append(variant)

    def get_variant(self, variant_id: str) -> Optional[ABVariant]:
        for v in self.variants:
            if v.variant_id == variant_id:
                return v
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "name": self.name,
            "status": self.status,
            "variant_count": len(self.variants),
            "winner": self.winner,
        }


class ABTestResult:
    """Result of an A/B test analysis."""

    __slots__ = ("test_id", "winner", "confidence", "lift",
                 "is_significant", "variant_results", "recommendation")

    def __init__(self, test_id: str = "") -> None:
        self.test_id = test_id
        self.winner: str = ""
        self.confidence: float = 0.0
        self.lift: float = 0.0
        self.is_significant: bool = False
        self.variant_results: List[Dict[str, Any]] = []
        self.recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "winner": self.winner,
            "confidence": round(self.confidence, 3),
            "lift": round(self.lift, 2),
            "is_significant": self.is_significant,
            "recommendation": self.recommendation,
        }


class ABTestEngine:
    """Run and analyze A/B tests."""

    SIGNIFICANCE_THRESHOLD = 0.95

    def __init__(self) -> None:
        self._tests: Dict[str, ABTest] = {}
        self._results: List[ABTestResult] = []
        self._analysis_count = 0

    def create_test(self, test_id: str, name: str, variant_names: List[str]) -> ABTest:
        test = ABTest(test_id, name)
        for i, vname in enumerate(variant_names):
            test.add_variant(ABVariant(f"{test_id}_v{i}", vname))
        self._tests[test_id] = test
        return test

    def start_test(self, test_id: str) -> bool:
        test = self._tests.get(test_id)
        if test and test.status == "draft":
            test.status = "running"
            test.started_at = time.time()
            return True
        return False

    def record_impression(self, test_id: str, variant_id: str) -> bool:
        test = self._tests.get(test_id)
        if not test:
            return False
        variant = test.get_variant(variant_id)
        if variant:
            variant.impressions += 1
            return True
        return False

    def record_conversion(self, test_id: str, variant_id: str, revenue: float = 0.0) -> bool:
        test = self._tests.get(test_id)
        if not test:
            return False
        variant = test.get_variant(variant_id)
        if variant:
            variant.conversions += 1
            variant.revenue += revenue
            return True
        return False

    def analyze(self, test_id: str) -> Optional[ABTestResult]:
        test = self._tests.get(test_id)
        if not test or len(test.variants) < 2:
            return None
        result = ABTestResult(test_id)
        control = test.variants[0]
        best_lift = 0.0
        for variant in test.variants[1:]:
            if control.conversions > 0 and variant.impressions > 0:
                lift = ((variant.conversion_rate - control.conversion_rate) / max(0.001, control.conversion_rate)) * 100
                if lift > best_lift:
                    best_lift = lift
                    result.winner = variant.variant_id
                    result.lift = lift
        total_impressions = sum(v.impressions for v in test.variants)
        total_conversions = sum(v.conversions for v in test.variants)
        if total_impressions > 100:
            result.confidence = min(0.99, 0.5 + (total_impressions / 10000) * 0.5)
        result.is_significant = result.confidence >= self.SIGNIFICANCE_THRESHOLD
        result.variant_results = [v.to_dict() for v in test.variants]
        if result.is_significant and result.winner:
            result.recommendation = f"Deploy variant {result.winner} (lift: {round(result.lift, 1)}%)"
        else:
            result.recommendation = "Need more data for statistical significance"
        self._results.append(result)
        self._analysis_count += 1
        return result

    def get_test(self, test_id: str) -> Optional[ABTest]:
        return self._tests.get(test_id)

    def get_all_tests(self) -> List[ABTest]:
        return list(self._tests.values())

    def get_results(self) -> List[ABTestResult]:
        return list(self._results)

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
