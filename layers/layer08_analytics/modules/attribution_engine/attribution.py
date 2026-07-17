"""Attribution Engine — Attribute conversions to marketing channels."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class AttributionTouchpoint:
    """A touchpoint in the customer journey."""

    __slots__ = ("touchpoint_id", "channel", "campaign", "timestamp",
                 "interaction_type", "revenue")

    def __init__(self, channel: str = "", campaign: str = "") -> None:
        self.touchpoint_id: str = f"tp_{int(time.time() * 1000) % 100000}"
        self.channel = channel
        self.campaign = campaign
        self.timestamp: float = time.time()
        self.interaction_type: str = "view"
        self.revenue: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "touchpoint_id": self.touchpoint_id,
            "channel": self.channel,
            "campaign": self.campaign,
            "interaction_type": self.interaction_type,
            "revenue": round(self.revenue, 2),
        }


class AttributionResult:
    """Result of an attribution analysis."""

    __slots__ = ("channel", "total_revenue", "touchpoint_count",
                 "first_touch_revenue", "last_touch_revenue",
                 "linear_revenue", "weighted_revenue")

    def __init__(self, channel: str = "") -> None:
        self.channel = channel
        self.total_revenue: float = 0.0
        self.touchpoint_count: int = 0
        self.first_touch_revenue: float = 0.0
        self.last_touch_revenue: float = 0.0
        self.linear_revenue: float = 0.0
        self.weighted_revenue: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel": self.channel,
            "total_revenue": round(self.total_revenue, 2),
            "touchpoint_count": self.touchpoint_count,
            "first_touch_revenue": round(self.first_touch_revenue, 2),
            "last_touch_revenue": round(self.last_touch_revenue, 2),
            "linear_revenue": round(self.linear_revenue, 2),
            "weighted_revenue": round(self.weighted_revenue, 2),
        }


class AttributionEngine:
    """Attribute conversions to marketing channels using various models."""

    def __init__(self) -> None:
        self._touchpoints: Dict[str, List[AttributionTouchpoint]] = {}
        self._results: List[AttributionResult] = []
        self._analysis_count = 0

    def add_touchpoint(self, customer_id: str, touchpoint: AttributionTouchpoint) -> None:
        self._touchpoints.setdefault(customer_id, []).append(touchpoint)

    def analyze_first_touch(self) -> List[AttributionResult]:
        return self._analyze("first_touch")

    def analyze_last_touch(self) -> List[AttributionResult]:
        return self._analyze("last_touch")

    def analyze_linear(self) -> List[AttributionResult]:
        return self._analyze("linear")

    def analyze_weighted(self) -> List[AttributionResult]:
        return self._analyze("weighted")

    def _analyze(self, model: str) -> List[AttributionResult]:
        channel_data: Dict[str, Dict[str, float]] = {}
        for customer_id, touchpoints in self._touchpoints.items():
            if not touchpoints:
                continue
            total_revenue = sum(tp.revenue for tp in touchpoints)
            channels = list(set(tp.channel for tp in touchpoints))
            for channel in channels:
                if channel not in channel_data:
                    channel_data[channel] = {
                        "touchpoint_count": 0,
                        "first_touch_revenue": 0.0,
                        "last_touch_revenue": 0.0,
                        "linear_revenue": 0.0,
                        "weighted_revenue": 0.0,
                    }
                channel_touchpoints = [tp for tp in touchpoints if tp.channel == channel]
                channel_data[channel]["touchpoint_count"] += len(channel_touchpoints)
                if model == "first_touch":
                    if touchpoints[0].channel == channel:
                        channel_data[channel]["first_touch_revenue"] += total_revenue
                elif model == "last_touch":
                    if touchpoints[-1].channel == channel:
                        channel_data[channel]["last_touch_revenue"] += total_revenue
                elif model == "linear":
                    share = total_revenue / len(channels)
                    channel_data[channel]["linear_revenue"] += share
                elif model == "weighted":
                    weights = self._position_weights(len(touchpoints))
                    for i, tp in enumerate(touchpoints):
                        if tp.channel == channel:
                            channel_data[channel]["weighted_revenue"] += total_revenue * weights[i]
        results = []
        for channel, data in channel_data.items():
            r = AttributionResult(channel)
            r.touchpoint_count = int(data["touchpoint_count"])
            r.first_touch_revenue = data["first_touch_revenue"]
            r.last_touch_revenue = data["last_touch_revenue"]
            r.linear_revenue = data["linear_revenue"]
            r.weighted_revenue = data["weighted_revenue"]
            r.total_revenue = r.first_touch_revenue + r.last_touch_revenue
            results.append(r)
        results.sort(key=lambda x: x.weighted_revenue, reverse=True)
        self._results = results
        self._analysis_count += 1
        return results

    def _position_weights(self, length: int) -> List[float]:
        if length <= 1:
            return [1.0]
        weights = []
        for i in range(length):
            if i == 0:
                weights.append(0.3)
            elif i == length - 1:
                weights.append(0.4)
            else:
                weights.append(0.3 / max(1, length - 2))
        total = sum(weights)
        return [w / total for w in weights]

    def get_touchpoints(self, customer_id: str) -> List[AttributionTouchpoint]:
        return list(self._touchpoints.get(customer_id, []))

    def get_results(self) -> List[AttributionResult]:
        return list(self._results)

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
