"""Statistically valid A/B experiment engine."""
from __future__ import annotations
import math
import time
from threading import RLock
from typing import Any, Dict, List, Optional


class ABVariant:
    __slots__ = ("variant_id", "name", "impressions", "conversions", "revenue", "metadata")
    def __init__(self, variant_id: str = "", name: str = "") -> None:
        if not variant_id.strip(): raise ValueError("variant_id is required")
        self.variant_id, self.name = variant_id, name
        self.impressions = self.conversions = 0
        self.revenue = 0.0
        self.metadata: Dict[str, Any] = {}
    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.impressions * 100 if self.impressions else 0.0
    @property
    def revenue_per_impression(self) -> float:
        return self.revenue / self.impressions if self.impressions else 0.0
    def to_dict(self) -> Dict[str, Any]:
        return {"variant_id": self.variant_id, "name": self.name, "impressions": self.impressions,
                "conversions": self.conversions, "conversion_rate": round(self.conversion_rate, 3),
                "revenue": round(self.revenue, 2)}


class ABTest:
    __slots__ = ("test_id", "name", "variants", "status", "started_at", "ended_at", "winner", "metadata")
    def __init__(self, test_id: str = "", name: str = "") -> None:
        if not test_id.strip(): raise ValueError("test_id is required")
        self.test_id, self.name = test_id, name
        self.variants: List[ABVariant] = []
        self.status, self.started_at, self.ended_at, self.winner = "draft", 0.0, 0.0, None
        self.metadata: Dict[str, Any] = {}
    def add_variant(self, variant: ABVariant) -> None:
        if any(v.variant_id == variant.variant_id for v in self.variants): raise ValueError("duplicate variant")
        self.variants.append(variant)
    def get_variant(self, variant_id: str) -> Optional[ABVariant]:
        return next((v for v in self.variants if v.variant_id == variant_id), None)
    def to_dict(self) -> Dict[str, Any]:
        return {"test_id": self.test_id, "name": self.name, "status": self.status,
                "variant_count": len(self.variants), "winner": self.winner}


class ABTestResult:
    __slots__ = ("test_id", "winner", "confidence", "lift", "is_significant", "variant_results", "recommendation")
    def __init__(self, test_id: str = "") -> None:
        self.test_id, self.winner, self.confidence, self.lift = test_id, "", 0.0, 0.0
        self.is_significant = False
        self.variant_results: List[Dict[str, Any]] = []
        self.recommendation = ""
    def to_dict(self) -> Dict[str, Any]:
        return {"test_id": self.test_id, "winner": self.winner, "confidence": round(self.confidence, 4),
                "lift": round(self.lift, 2), "is_significant": self.is_significant,
                "recommendation": self.recommendation}


class ABTestEngine:
    SIGNIFICANCE_THRESHOLD = 0.95
    def __init__(self) -> None:
        self._tests: Dict[str, ABTest] = {}
        self._results: List[ABTestResult] = []
        self._analysis_count = 0
        self._lock = RLock()
    def create_test(self, test_id: str, name: str, variant_names: List[str]) -> ABTest:
        if len(variant_names) < 2 or any(not n.strip() for n in variant_names): raise ValueError("at least two non-empty variants required")
        with self._lock:
            if test_id in self._tests: raise ValueError(f"test already exists: {test_id}")
            test = ABTest(test_id, name)
            for i, name_ in enumerate(variant_names): test.add_variant(ABVariant(f"{test_id}_v{i}", name_))
            self._tests[test_id] = test
            return test
    def start_test(self, test_id: str) -> bool:
        with self._lock:
            test = self._tests.get(test_id)
            if not test or test.status != "draft": return False
            test.status, test.started_at = "running", time.time()
            return True
    def record_impression(self, test_id: str, variant_id: str) -> bool:
        with self._lock:
            test = self._tests.get(test_id); variant = test.get_variant(variant_id) if test else None
            if not test or not variant or test.status != "running": return False
            variant.impressions += 1; return True
    def record_conversion(self, test_id: str, variant_id: str, revenue: float = 0.0) -> bool:
        if revenue < 0 or not math.isfinite(float(revenue)): raise ValueError("revenue must be finite and non-negative")
        with self._lock:
            test = self._tests.get(test_id); variant = test.get_variant(variant_id) if test else None
            if not test or not variant or test.status != "running" or variant.conversions >= variant.impressions: return False
            variant.conversions += 1; variant.revenue += float(revenue); return True
    def analyze(self, test_id: str) -> Optional[ABTestResult]:
        with self._lock: test = self._tests.get(test_id)
        if not test or len(test.variants) < 2: return None
        result = ABTestResult(test_id); result.variant_results = [v.to_dict() for v in test.variants]
        control = test.variants[0]
        best = max(test.variants, key=lambda v: v.conversion_rate)
        if best is not control and control.impressions and best.impressions:
            p1, p2 = control.conversions/control.impressions, best.conversions/best.impressions
            pooled = (control.conversions + best.conversions) / (control.impressions + best.impressions)
            se = math.sqrt(pooled * (1 - pooled) * (1/control.impressions + 1/best.impressions))
            if se > 0:
                z = abs(p2 - p1) / se
                result.confidence = math.erf(z / math.sqrt(2))
                result.is_significant = result.confidence >= self.SIGNIFICANCE_THRESHOLD
            result.lift = ((p2-p1)/p1*100) if p1 else 0.0
            if result.is_significant: result.winner = best.variant_id
        result.recommendation = (
            f"Evidence supports variant {result.winner}" if result.is_significant and result.winner
            else "Insufficient statistical evidence for a winner"
        )
        with self._lock:
            self._results.append(result); self._analysis_count += 1
        return result
    def get_test(self, test_id: str) -> Optional[ABTest]:
        with self._lock: return self._tests.get(test_id)
    def get_all_tests(self) -> List[ABTest]:
        with self._lock: return list(self._tests.values())
    def get_results(self) -> List[ABTestResult]:
        with self._lock: return list(self._results)
    @property
    def analysis_count(self) -> int:
        with self._lock: return self._analysis_count
