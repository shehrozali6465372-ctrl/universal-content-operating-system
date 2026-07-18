"""optimizer.py — Query optimization."""
from __future__ import annotations
from typing import Any, Dict, List


class OptimizationSuggestion:
    """A query optimization suggestion."""
    __slots__ = ("suggestion_id", "query_pattern", "issue", "recommendation", "impact")
    _counter = 0

    def __init__(self, query_pattern: str, issue: str, recommendation: str,
                 impact: str = "medium") -> None:
        OptimizationSuggestion._counter += 1
        self.suggestion_id: int = OptimizationSuggestion._counter
        self.query_pattern = query_pattern
        self.issue = issue
        self.recommendation = recommendation
        self.impact = impact

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.suggestion_id, "issue": self.issue,
                "recommendation": self.recommendation, "impact": self.impact}


class QueryOptimizer:
    """Analyzes and optimizes queries."""

    def __init__(self) -> None:
        self._suggestions: List[OptimizationSuggestion] = []
        self._rules: List[Dict[str, str]] = [
            {"pattern": "SELECT *", "issue": "Full column scan",
             "recommendation": "Select specific columns"},
            {"pattern": "LIKE '%...%'", "issue": "Leading wildcard",
             "recommendation": "Use full-text search"},
            {"pattern": "ORDER BY", "issue": "No index hint",
             "recommendation": "Add index on ORDER BY columns"},
        ]

    def analyze(self, sql: str) -> List[OptimizationSuggestion]:
        results = []
        for rule in self._rules:
            if rule["pattern"].lower() in sql.lower():
                s = OptimizationSuggestion(sql[:100], rule["issue"],
                                            rule["recommendation"])
                results.append(s)
                self._suggestions.append(s)
        return results

    def get_all_suggestions(self) -> List[OptimizationSuggestion]:
        return list(self._suggestions)

    def get_rules(self) -> List[Dict[str, str]]:
        return list(self._rules)
