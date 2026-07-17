"""Metric Engine — Calculate, aggregate, and transform metrics."""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional


class MetricDefinition:
    """Definition of a calculable metric."""

    __slots__ = ("metric_id", "name", "formula", "description",
                 "unit", "category", "higher_is_better")

    def __init__(self, metric_id: str = "", name: str = "", formula: str = "sum") -> None:
        self.metric_id = metric_id
        self.name = name
        self.formula = formula
        self.description: str = ""
        self.unit: str = ""
        self.category: str = "general"
        self.higher_is_better: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "formula": self.formula,
            "unit": self.unit,
            "category": self.category,
        }


class MetricValue:
    """Calculated metric value with context."""

    __slots__ = ("metric_id", "value", "timestamp", "dimensions", "formula_used")

    def __init__(self, metric_id: str = "", value: float = 0.0) -> None:
        self.metric_id = metric_id
        self.value = value
        self.timestamp: float = 0.0
        self.dimensions: Dict[str, str] = {}
        self.formula_used: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "value": round(self.value, 4),
            "formula_used": self.formula_used,
        }


class MetricEngine:
    """Calculate, aggregate, and transform metrics."""

    def __init__(self) -> None:
        self._definitions: Dict[str, MetricDefinition] = {}
        self._values: List[MetricValue] = []
        self._calculation_count = 0

    def define(self, definition: MetricDefinition) -> None:
        self._definitions[definition.metric_id] = definition

    def get_definition(self, metric_id: str) -> Optional[MetricDefinition]:
        return self._definitions.get(metric_id)

    def calculate(self, metric_id: str, values: List[float]) -> MetricValue:
        definition = self._definitions.get(metric_id)
        formula = definition.formula if definition else "sum"
        result = MetricValue(metric_id, 0.0)
        result.formula_used = formula

        if not values:
            result.value = 0.0
            self._values.append(result)
            self._calculation_count += 1
            return result

        if formula == "sum":
            result.value = sum(values)
        elif formula == "avg" or formula == "mean":
            result.value = sum(values) / len(values)
        elif formula == "min":
            result.value = min(values)
        elif formula == "max":
            result.value = max(values)
        elif formula == "count":
            result.value = len(values)
        elif formula == "median":
            sorted_vals = sorted(values)
            mid = len(sorted_vals) // 2
            result.value = sorted_vals[mid] if len(sorted_vals) % 2 else (sorted_vals[mid-1] + sorted_vals[mid]) / 2
        elif formula == "std_dev":
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            result.value = math.sqrt(variance)
        elif formula == "p95":
            sorted_vals = sorted(values)
            idx = int(len(sorted_vals) * 0.95)
            result.value = sorted_vals[min(idx, len(sorted_vals) - 1)]
        elif formula == "p99":
            sorted_vals = sorted(values)
            idx = int(len(sorted_vals) * 0.99)
            result.value = sorted_vals[min(idx, len(sorted_vals) - 1)]
        elif formula == "growth_rate":
            if len(values) >= 2 and values[-2] != 0:
                result.value = ((values[-1] - values[-2]) / abs(values[-2])) * 100
            else:
                result.value = 0.0
        else:
            result.value = sum(values)

        self._values.append(result)
        self._calculation_count += 1
        return result

    def aggregate(self, metric_id: str, data_points: List[Dict[str, Any]], formula: str = "sum") -> MetricValue:
        values = [d.get("value", 0.0) for d in data_points if isinstance(d.get("value"), (int, float))]
        result = self.calculate(metric_id, values)
        result.formula_used = formula
        return result

    def get_all_definitions(self) -> List[MetricDefinition]:
        return list(self._definitions.values())

    def get_recent_values(self, metric_id: str, limit: int = 10) -> List[MetricValue]:
        return [v for v in self._values if v.metric_id == metric_id][-limit:]

    @property
    def calculation_count(self) -> int:
        return self._calculation_count
