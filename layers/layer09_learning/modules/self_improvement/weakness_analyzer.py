"""Weakness Analyzer — Analyze systemic weaknesses across content."""
from __future__ import annotations
from typing import Any, Dict, List
import itertools


class Weakness:
    """A detected weakness with analysis."""

    __slots__ = ("weakness_id", "area", "severity", "frequency",
                 "impact_score", "description", "suggestion", "evidence_count")

    _counter = 0

    def __init__(self, area: str = "") -> None:
        next(_WA)
        self.weakness_id: str = f"wka_{next(_WA)}"
        self.area = area
        self.severity: str = "medium"
        self.frequency: int = 0
        self.impact_score: float = 0.0
        self.description: str = ""
        self.suggestion: str = ""
        self.evidence_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weakness_id": self.weakness_id,
            "area": self.area,
            "severity": self.severity,
            "frequency": self.frequency,
            "impact_score": round(self.impact_score, 3),
            "evidence_count": self.evidence_count,
        }


_WA = itertools.count(1)

class WeaknessAnalyzer:
    """Analyze recurring weaknesses from historical data."""

    def __init__(self) -> None:
        self._weaknesses: List[Weakness] = []
        self._analysis_count: int = 0

    def analyze(self, issues: List[Dict[str, Any]],
                min_frequency: int = 2) -> List[Weakness]:
        self._weaknesses.clear()
        area_issues: Dict[str, List[Dict[str, Any]]] = {}
        for issue in issues:
            area = issue.get("area", "unknown")
            area_issues.setdefault(area, []).append(issue)

        for area, area_list in area_issues.items():
            if len(area_list) >= min_frequency:
                w = Weakness(area)
                w.frequency = len(area_list)
                w.evidence_count = len(area_list)
                severities = [i.get("severity", "medium") for i in area_list]
                if "critical" in severities:
                    w.severity = "critical"
                elif "high" in severities:
                    w.severity = "high"
                elif "medium" in severities:
                    w.severity = "medium"
                else:
                    w.severity = "low"
                w.impact_score = round(
                    sum(i.get("impact", 0.5) for i in area_list) / len(area_list), 3,
                )
                w.description = f"Recurring {area} issues ({w.frequency} times, severity: {w.severity})"
                w.suggestion = f"Address root cause of {area} problems"
                self._weaknesses.append(w)

        self._weaknesses.sort(key=lambda w: w.impact_score, reverse=True)
        self._analysis_count += 1
        return list(self._weaknesses)

    def get_by_severity(self, severity: str) -> List[Weakness]:
        return [w for w in self._weaknesses if w.severity == severity]

    def get_weaknesses(self) -> List[Weakness]:
        return list(self._weaknesses)

    @property
    def weakness_count(self) -> int:
        return len(self._weaknesses)

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
