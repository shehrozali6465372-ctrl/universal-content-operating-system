"""Validated metric calculation and aggregation."""
from __future__ import annotations

import math
from threading import RLock
from typing import Any, Dict, List, Optional

from layers.layer08_analytics.modules.exceptions import MetricCalculationError


class MetricDefinition:
    __slots__ = ("metric_id", "name", "formula", "description", "unit", "category", "higher_is_better")

    SUPPORTED = {"sum", "avg", "mean", "min", "max", "count", "median", "std_dev", "p95", "p99", "growth_rate"}

    def __init__(self, metric_id: str = "", name: str = "", formula: str = "sum") -> None:
        if not metric_id.strip():
            raise ValueError("metric_id is required")
        if formula not in self.SUPPORTED:
            raise ValueError(f"unsupported metric formula: {formula}")
        self.metric_id, self.name, self.formula = metric_id.strip(), name.strip(), formula
        self.description, self.unit, self.category = "", "", "general"
        self.higher_is_better = True

    def to_dict(self) -> Dict[str, Any]:
        return {"metric_id": self.metric_id, "name": self.name, "formula": self.formula,
                "unit": self.unit, "category": self.category}


class MetricValue:
    __slots__ = ("metric_id", "value", "timestamp", "dimensions", "formula_used")

    def __init__(self, metric_id: str = "", value: float = 0.0) -> None:
        self.metric_id, self.value = metric_id, float(value)
        self.timestamp = 0.0
        self.dimensions: Dict[str, str] = {}
        self.formula_used = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"metric_id": self.metric_id, "value": round(self.value, 4),
                "formula_used": self.formula_used}


class MetricEngine:
    def __init__(self) -> None:
        self._definitions: Dict[str, MetricDefinition] = {}
        self._values: List[MetricValue] = []
        self._calculation_count = 0
        self._lock = RLock()

    def define(self, definition: MetricDefinition) -> None:
        with self._lock:
            if definition.metric_id in self._definitions:
                raise ValueError(f"metric already defined: {definition.metric_id}")
            self._definitions[definition.metric_id] = definition

    def get_definition(self, metric_id: str) -> Optional[MetricDefinition]:
        with self._lock:
            return self._definitions.get(metric_id)

    def calculate(self, metric_id: str, values: List[float], formula: Optional[str] = None) -> MetricValue:
        definition = self.get_definition(metric_id)
        selected = formula or (definition.formula if definition else "sum")
        if selected not in MetricDefinition.SUPPORTED:
            raise MetricCalculationError(f"unsupported formula: {selected}")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in values):
            raise MetricCalculationError("all metric values must be finite numbers")
        vals = [float(v) for v in values]
        result = MetricValue(metric_id)
        result.formula_used = selected
        try:
            if not vals:
                result.value = 0.0
            elif selected == "sum":
                result.value = sum(vals)
            elif selected in {"avg", "mean"}:
                result.value = sum(vals) / len(vals)
            elif selected == "min":
                result.value = min(vals)
            elif selected == "max":
                result.value = max(vals)
            elif selected == "count":
                result.value = float(len(vals))
            elif selected == "median":
                ordered = sorted(vals); mid = len(ordered) // 2
                result.value = ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
            elif selected == "std_dev":
                mean = sum(vals) / len(vals)
                result.value = math.sqrt(sum((x - mean) ** 2 for x in vals) / len(vals))
            elif selected in {"p95", "p99"}:
                ordered = sorted(vals)
                rank = (0.95 if selected == "p95" else 0.99) * (len(ordered) - 1)
                lo, hi = math.floor(rank), math.ceil(rank)
                result.value = ordered[lo] if lo == hi else ordered[lo] + (ordered[hi] - ordered[lo]) * (rank - lo)
            elif selected == "growth_rate":
                result.value = ((vals[-1] - vals[-2]) / abs(vals[-2])) * 100 if len(vals) >= 2 and vals[-2] != 0 else 0.0
            if not math.isfinite(result.value):
                raise MetricCalculationError("metric result is not finite")
        except (ZeroDivisionError, ValueError) as exc:
            raise MetricCalculationError(f"failed to calculate {selected}") from exc
        result.timestamp = __import__("time").time()
        with self._lock:
            self._values.append(result)
            self._calculation_count += 1
        return result

    def aggregate(self, metric_id: str, data_points: List[Dict[str, Any]], formula: Optional[str] = None) -> MetricValue:
        values = [d["value"] for d in data_points if isinstance(d, dict) and "value" in d]
        return self.calculate(metric_id, values, formula=formula)

    def get_all_definitions(self) -> List[MetricDefinition]:
        with self._lock:
            return list(self._definitions.values())

    def get_recent_values(self, metric_id: str, limit: int = 10) -> List[MetricValue]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        with self._lock:
            values = [v for v in self._values if v.metric_id == metric_id]
        return values[-limit:] if limit else []

    @property
    def calculation_count(self) -> int:
        with self._lock:
            return self._calculation_count
