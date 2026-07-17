"""Funnel Analyzer — Analyze conversion funnels and identify drop-off points."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class FunnelStep:
    """A step in a conversion funnel."""

    __slots__ = ("step_id", "name", "order", "entries", "exits",
                 "conversions", "revenue")

    def __init__(self, step_id: str = "", name: str = "", order: int = 0) -> None:
        self.step_id = step_id
        self.name = name
        self.order = order
        self.entries: int = 0
        self.exits: int = 0
        self.conversions: int = 0
        self.revenue: float = 0.0

    @property
    def conversion_rate(self) -> float:
        return (self.conversions / max(1, self.entries)) * 100

    @property
    def drop_off_rate(self) -> float:
        return ((self.entries - self.exits) / max(1, self.entries)) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "order": self.order,
            "entries": self.entries,
            "exits": self.exits,
            "conversions": self.conversions,
            "conversion_rate": round(self.conversion_rate, 2),
            "drop_off_rate": round(self.drop_off_rate, 2),
        }


class FunnelDefinition:
    """A conversion funnel definition."""

    __slots__ = ("funnel_id", "name", "steps", "status", "created_at")

    def __init__(self, funnel_id: str = "", name: str = "") -> None:
        self.funnel_id = funnel_id
        self.name = name
        self.steps: List[FunnelStep] = []
        self.status: str = "active"
        self.created_at: float = time.time()

    def add_step(self, step: FunnelStep) -> None:
        self.steps.append(step)
        self.steps.sort(key=lambda s: s.order)

    def get_step(self, step_id: str) -> Optional[FunnelStep]:
        for s in self.steps:
            if s.step_id == step_id:
                return s
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "funnel_id": self.funnel_id,
            "name": self.name,
            "step_count": len(self.steps),
            "status": self.status,
        }


class FunnelResult:
    """Result of a funnel analysis."""

    __slots__ = ("funnel_id", "overall_conversion", "total_entries",
                 "total_conversions", "biggest_drop_off", "step_results",
                 "insights")

    def __init__(self, funnel_id: str = "") -> None:
        self.funnel_id = funnel_id
        self.overall_conversion: float = 0.0
        self.total_entries: int = 0
        self.total_conversions: int = 0
        self.biggest_drop_off: str = ""
        self.step_results: List[Dict[str, Any]] = []
        self.insights: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "funnel_id": self.funnel_id,
            "overall_conversion": round(self.overall_conversion, 2),
            "total_entries": self.total_entries,
            "total_conversions": self.total_conversions,
            "biggest_drop_off": self.biggest_drop_off,
            "insight_count": len(self.insights),
        }


class FunnelAnalyzer:
    """Analyze conversion funnels."""

    def __init__(self) -> None:
        self._funnels: Dict[str, FunnelDefinition] = {}
        self._results: List[FunnelResult] = []
        self._analysis_count = 0

    def create_funnel(self, funnel_id: str, name: str, step_names: List[str]) -> FunnelDefinition:
        funnel = FunnelDefinition(funnel_id, name)
        for i, sname in enumerate(step_names):
            funnel.add_step(FunnelStep(f"{funnel_id}_s{i}", sname, i))
        self._funnels[funnel_id] = funnel
        return funnel

    def update_step(self, funnel_id: str, step_id: str, entries: int, exits: int, conversions: int = 0) -> bool:
        funnel = self._funnels.get(funnel_id)
        if not funnel:
            return False
        step = funnel.get_step(step_id)
        if step:
            step.entries = entries
            step.exits = exits
            step.conversions = conversions
            return True
        return False

    def analyze(self, funnel_id: str) -> Optional[FunnelResult]:
        funnel = self._funnels.get(funnel_id)
        if not funnel or not funnel.steps:
            return None
        result = FunnelResult(funnel_id)
        first_step = funnel.steps[0]
        last_step = funnel.steps[-1]
        result.total_entries = first_step.entries
        result.total_conversions = last_step.conversions
        result.overall_conversion = (last_step.conversions / max(1, first_step.entries)) * 100

        biggest_drop = 0.0
        for step in funnel.steps:
            drop = step.entries - step.exits
            if drop > biggest_drop:
                biggest_drop = drop
                result.biggest_drop_off = step.name
            result.step_results.append(step.to_dict())

        if result.overall_conversion < 1.0:
            result.insights.append("Overall conversion is very low — review the entire funnel")
        if result.biggest_drop_off:
            result.insights.append(f"Biggest drop-off at: {result.biggest_drop_off}")

        self._results.append(result)
        self._analysis_count += 1
        return result

    def get_funnel(self, funnel_id: str) -> Optional[FunnelDefinition]:
        return self._funnels.get(funnel_id)

    def get_all_funnels(self) -> List[FunnelDefinition]:
        return list(self._funnels.values())

    def get_results(self) -> List[FunnelResult]:
        return list(self._results)

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
