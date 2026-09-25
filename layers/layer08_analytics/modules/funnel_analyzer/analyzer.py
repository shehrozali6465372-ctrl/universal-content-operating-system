"""Validated conversion funnel analysis."""
from __future__ import annotations
import time
import uuid
from threading import RLock
from typing import Any, Dict, List, Optional


class FunnelStep:
    __slots__ = ("step_id", "name", "order", "entries", "exits", "conversions", "revenue")
    def __init__(self, step_id: str = "", name: str = "", order: int = 0) -> None:
        if not step_id.strip(): raise ValueError("step_id is required")
        self.step_id, self.name, self.order = step_id, name, order
        self.entries = self.exits = self.conversions = 0
        self.revenue = 0.0
    @property
    def conversion_rate(self) -> float: return self.conversions / self.entries * 100 if self.entries else 0.0
    @property
    def drop_off_rate(self) -> float: return max(0.0, self.entries - self.exits) / self.entries * 100 if self.entries else 0.0
    def to_dict(self) -> Dict[str, Any]:
        return {"step_id": self.step_id, "name": self.name, "order": self.order,
                "entries": self.entries, "exits": self.exits, "conversions": self.conversions,
                "conversion_rate": round(self.conversion_rate, 2), "drop_off_rate": round(self.drop_off_rate, 2)}


class FunnelDefinition:
    __slots__ = ("funnel_id", "name", "steps", "status", "created_at")
    def __init__(self, funnel_id: str = "", name: str = "") -> None:
        if not funnel_id.strip(): raise ValueError("funnel_id is required")
        self.funnel_id, self.name, self.steps = funnel_id, name, []
        self.status, self.created_at = "active", time.time()
    def add_step(self, step: FunnelStep) -> None:
        if any(s.step_id == step.step_id for s in self.steps): raise ValueError("duplicate step")
        self.steps.append(step); self.steps.sort(key=lambda s: s.order)
    def get_step(self, step_id: str) -> Optional[FunnelStep]:
        return next((s for s in self.steps if s.step_id == step_id), None)
    def to_dict(self) -> Dict[str, Any]:
        return {"funnel_id": self.funnel_id, "name": self.name, "step_count": len(self.steps), "status": self.status}


class FunnelResult:
    __slots__ = ("funnel_id", "overall_conversion", "total_entries", "total_conversions",
                 "biggest_drop_off", "step_results", "insights")
    def __init__(self, funnel_id: str = "") -> None:
        self.funnel_id, self.overall_conversion = funnel_id, 0.0
        self.total_entries = self.total_conversions = 0
        self.biggest_drop_off = ""; self.step_results: List[Dict[str, Any]] = []; self.insights: List[str] = []
    def to_dict(self) -> Dict[str, Any]:
        return {"funnel_id": self.funnel_id, "overall_conversion": round(self.overall_conversion, 2),
                "total_entries": self.total_entries, "total_conversions": self.total_conversions,
                "biggest_drop_off": self.biggest_drop_off, "insight_count": len(self.insights)}


class FunnelAnalyzer:
    def __init__(self) -> None:
        self._funnels: Dict[str, FunnelDefinition] = {}; self._results: List[FunnelResult] = []
        self._analysis_count = 0; self._lock = RLock()
    def create_funnel(self, funnel_id: str, name: str, step_names: List[str]) -> FunnelDefinition:
        if len(step_names) < 2 or any(not s.strip() for s in step_names): raise ValueError("at least two non-empty steps required")
        with self._lock:
            if funnel_id in self._funnels: raise ValueError(f"funnel already exists: {funnel_id}")
            funnel = FunnelDefinition(funnel_id, name)
            for i, sname in enumerate(step_names): funnel.add_step(FunnelStep(f"{funnel_id}_s{i}", sname, i))
            self._funnels[funnel_id] = funnel; return funnel
    def update_step(self, funnel_id: str, step_id: str, entries: int, exits: int, conversions: int = 0) -> bool:
        if min(entries, exits, conversions) < 0 or exits > entries or conversions > entries: raise ValueError("invalid funnel counts")
        with self._lock:
            funnel = self._funnels.get(funnel_id); step = funnel.get_step(step_id) if funnel else None
            if not funnel or not step: return False
            step.entries, step.exits, step.conversions = entries, exits, conversions; return True
    def analyze(self, funnel_id: str) -> Optional[FunnelResult]:
        with self._lock: funnel = self._funnels.get(funnel_id)
        if not funnel or not funnel.steps: return None
        result = FunnelResult(funnel_id); first, last = funnel.steps[0], funnel.steps[-1]
        result.total_entries, result.total_conversions = first.entries, last.conversions
        result.overall_conversion = last.conversions / first.entries * 100 if first.entries else 0.0
        biggest = -1.0
        for step in funnel.steps:
            drop = max(0, step.entries-step.exits)
            if drop > biggest: biggest, result.biggest_drop_off = drop, step.name
            result.step_results.append(step.to_dict())
        if result.overall_conversion < 1.0 and result.total_entries: result.insights.append("overall_conversion_below_one_percent")
        if result.biggest_drop_off: result.insights.append(f"biggest_drop_off:{result.biggest_drop_off}")
        with self._lock: self._results.append(result); self._analysis_count += 1
        return result
    def get_funnel(self, funnel_id: str) -> Optional[FunnelDefinition]:
        with self._lock: return self._funnels.get(funnel_id)
    def get_all_funnels(self) -> List[FunnelDefinition]:
        with self._lock: return list(self._funnels.values())
    def get_results(self) -> List[FunnelResult]:
        with self._lock: return list(self._results)
    @property
    def analysis_count(self) -> int:
        with self._lock: return self._analysis_count
