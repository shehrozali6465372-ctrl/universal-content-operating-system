"""provider_ab_test.py — A/B testing between providers."""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional


class ABTest:
    """A/B test between two providers."""
    __slots__ = ("test_id", "provider_a", "provider_b", "split_ratio",
                 "results", "status", "winner")

    def __init__(self, test_id: str, provider_a: str, provider_b: str,
                 split_ratio: float = 0.5) -> None:
        self.test_id = test_id
        self.provider_a = provider_a
        self.provider_b = provider_b
        self.split_ratio = split_ratio
        self.results: Dict[str, List[float]] = {"a": [], "b": []}
        self.status: str = "running"
        self.winner: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"test_id": self.test_id, "provider_a": self.provider_a,
                "provider_b": self.provider_b, "status": self.status,
                "winner": self.winner, "a_count": len(self.results["a"]),
                "b_count": len(self.results["b"])}


class ProviderABTest:
    """Manages A/B tests between providers."""

    def __init__(self) -> None:
        self._tests: Dict[str, ABTest] = {}

    def create_test(self, test_id: str, provider_a: str, provider_b: str,
                    split_ratio: float = 0.5) -> ABTest:
        test = ABTest(test_id, provider_a, provider_b, split_ratio)
        self._tests[test_id] = test
        return test

    def select_provider(self, test_id: str) -> str:
        test = self._tests.get(test_id)
        if not test:
            return ""
        return test.provider_a if random.random() < test.split_ratio else test.provider_b

    def record_result(self, test_id: str, provider: str, score: float) -> None:
        test = self._tests.get(test_id)
        if test:
            key = "a" if provider == test.provider_a else "b"
            test.results[key].append(score)

    def evaluate(self, test_id: str) -> Optional[str]:
        test = self._tests.get(test_id)
        if not test:
            return None
        avg_a = sum(test.results["a"]) / len(test.results["a"]) if test.results["a"] else 0
        avg_b = sum(test.results["b"]) / len(test.results["b"]) if test.results["b"] else 0
        test.winner = test.provider_a if avg_a >= avg_b else test.provider_b
        test.status = "completed"
        return test.winner

    def get_test(self, test_id: str) -> Optional[ABTest]:
        return self._tests.get(test_id)

    def get_all_tests(self) -> List[ABTest]:
        return list(self._tests.values())
