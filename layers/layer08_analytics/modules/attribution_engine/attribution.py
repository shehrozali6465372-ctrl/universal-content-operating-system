"""Multi-model marketing attribution with conservation of revenue."""
from __future__ import annotations
import math
import time
import uuid
from threading import RLock
from typing import Any, Dict, List


class AttributionTouchpoint:
    __slots__ = ("touchpoint_id", "channel", "campaign", "timestamp", "interaction_type", "revenue")
    def __init__(self, channel: str = "", campaign: str = "") -> None:
        if not channel.strip(): raise ValueError("channel is required")
        self.touchpoint_id, self.channel, self.campaign = f"tp_{uuid.uuid4().hex}", channel.strip(), campaign.strip()
        self.timestamp, self.interaction_type, self.revenue = time.time(), "view", 0.0
    def to_dict(self) -> Dict[str, Any]:
        return {"touchpoint_id": self.touchpoint_id, "channel": self.channel, "campaign": self.campaign,
                "interaction_type": self.interaction_type, "revenue": round(self.revenue, 2)}


class AttributionResult:
    __slots__ = ("channel", "total_revenue", "touchpoint_count", "first_touch_revenue",
                 "last_touch_revenue", "linear_revenue", "weighted_revenue")
    def __init__(self, channel: str = "") -> None:
        self.channel = channel; self.total_revenue = 0.0; self.touchpoint_count = 0
        self.first_touch_revenue = self.last_touch_revenue = 0.0
        self.linear_revenue = self.weighted_revenue = 0.0
    def to_dict(self) -> Dict[str, Any]:
        return {"channel": self.channel, "total_revenue": round(self.total_revenue, 2),
                "touchpoint_count": self.touchpoint_count, "first_touch_revenue": round(self.first_touch_revenue, 2),
                "last_touch_revenue": round(self.last_touch_revenue, 2), "linear_revenue": round(self.linear_revenue, 2),
                "weighted_revenue": round(self.weighted_revenue, 2)}


class AttributionEngine:
    def __init__(self) -> None:
        self._touchpoints: Dict[str, List[AttributionTouchpoint]] = {}
        self._results: List[AttributionResult] = []; self._analysis_count = 0; self._lock = RLock()
    def add_touchpoint(self, customer_id: str, touchpoint: AttributionTouchpoint) -> None:
        if not customer_id.strip(): raise ValueError("customer_id is required")
        if touchpoint.revenue < 0 or not math.isfinite(float(touchpoint.revenue)): raise ValueError("revenue must be finite and non-negative")
        with self._lock: self._touchpoints.setdefault(customer_id.strip(), []).append(touchpoint)
    def analyze_first_touch(self) -> List[AttributionResult]: return self._analyze("first_touch")
    def analyze_last_touch(self) -> List[AttributionResult]: return self._analyze("last_touch")
    def analyze_linear(self) -> List[AttributionResult]: return self._analyze("linear")
    def analyze_weighted(self) -> List[AttributionResult]: return self._analyze("weighted")
    def _analyze(self, model: str) -> List[AttributionResult]:
        if model not in {"first_touch", "last_touch", "linear", "weighted"}: raise ValueError("unsupported attribution model")
        with self._lock: customers = {k: list(v) for k, v in self._touchpoints.items()}
        data: Dict[str, AttributionResult] = {}
        for touchpoints in customers.values():
            if not touchpoints: continue
            revenue = sum(tp.revenue for tp in touchpoints)
            weights = self._position_weights(len(touchpoints)) if model == "weighted" else []
            for index, tp in enumerate(touchpoints):
                result = data.setdefault(tp.channel, AttributionResult(tp.channel))
                result.touchpoint_count += 1
                if model == "first_touch" and index == 0: result.first_touch_revenue += revenue
                elif model == "last_touch" and index == len(touchpoints)-1: result.last_touch_revenue += revenue
                elif model == "linear": result.linear_revenue += revenue / len(touchpoints)
                elif model == "weighted": result.weighted_revenue += revenue * weights[index]
        results = list(data.values())
        for result in results:
            result.total_revenue = (
                result.first_touch_revenue + result.last_touch_revenue +
                result.linear_revenue + result.weighted_revenue
            )
        with self._lock: self._results = results; self._analysis_count += 1
        return list(results)
    @staticmethod
    def _position_weights(length: int) -> List[float]:
        if length <= 1: return [1.0]
        if length == 2: return [0.3, 0.7]
        weights = [0.3] + [0.3 / (length - 2)] * (length - 2) + [0.4]
        total = sum(weights)
        return [w / total for w in weights]
    def get_touchpoints(self, customer_id: str) -> List[AttributionTouchpoint]:
        with self._lock: return list(self._touchpoints.get(customer_id, []))
    def get_results(self) -> List[AttributionResult]:
        with self._lock: return list(self._results)
    @property
    def analysis_count(self) -> int:
        with self._lock: return self._analysis_count
