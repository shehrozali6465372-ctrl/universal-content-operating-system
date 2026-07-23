"""RevenuePredictionEngine — Predicts revenue per niche, affiliate, platform."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class NicheRevenuePrediction:
    __slots__ = ("niche", "predicted_monthly_revenue", "predicted_annual_revenue",
                 "best_affiliate", "best_platform", "confidence", "factors",
                 "low_estimate", "high_estimate", "assumptions", "updated_at")

    def __init__(self, niche: str) -> None:
        self.niche = niche
        self.predicted_monthly_revenue = 0.0
        self.predicted_annual_revenue = 0.0
        self.best_affiliate = ""
        self.best_platform = ""
        self.confidence = 0.0
        self.factors: Dict[str, float] = {}
        self.low_estimate = 0.0
        self.high_estimate = 0.0
        self.assumptions: List[str] = []
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "niche": self.niche,
            "monthly_revenue": round(self.predicted_monthly_revenue, 2),
            "annual_revenue": round(self.predicted_annual_revenue, 2),
            "best_affiliate": self.best_affiliate,
            "best_platform": self.best_platform,
            "confidence": round(self.confidence, 1),
            "range": {"low": round(self.low_estimate, 2), "high": round(self.high_estimate, 2)},
            "factors": self.factors,
        }


class AffiliatePrediction:
    __slots__ = ("affiliate", "niche", "conversion_rate", "epc", "avg_commission",
                 "monthly_clicks_predicted", "monthly_revenue_predicted",
                 "confidence", "data_points")

    def __init__(self, affiliate: str, niche: str = "") -> None:
        self.affiliate = affiliate
        self.niche = niche
        self.conversion_rate = 0.0
        self.epc = 0.0
        self.avg_commission = 0.0
        self.monthly_clicks_predicted = 0
        self.monthly_revenue_predicted = 0.0
        self.confidence = 0.0
        self.data_points = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "affiliate": self.affiliate, "niche": self.niche,
            "conversion_rate": round(self.conversion_rate, 2),
            "epc": round(self.epc, 4),
            "avg_commission": round(self.avg_commission, 2),
            "predicted_monthly_revenue": round(self.monthly_revenue_predicted, 2),
            "confidence": round(self.confidence, 1),
            "data_points": self.data_points,
        }


class PlatformPrediction:
    __slots__ = ("platform", "niche", "avg_reach", "avg_engagement_rate",
                 "affiliate_click_rate", "monthly_content_count",
                 "predicted_monthly_revenue", "roi_per_post", "confidence")

    def __init__(self, platform: str, niche: str = "") -> None:
        self.platform = platform
        self.niche = niche
        self.avg_reach = 0
        self.avg_engagement_rate = 0.0
        self.affiliate_click_rate = 0.0
        self.monthly_content_count = 0
        self.predicted_monthly_revenue = 0.0
        self.roi_per_post = 0.0
        self.confidence = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform, "niche": self.niche,
            "avg_reach": self.avg_reach,
            "engagement_rate": round(self.avg_engagement_rate, 2),
            "affiliate_click_rate": round(self.affiliate_click_rate, 2),
            "monthly_content": self.monthly_content_count,
            "predicted_revenue": round(self.predicted_monthly_revenue, 2),
            "roi_per_post": round(self.roi_per_post, 2),
            "confidence": round(self.confidence, 1),
        }


class RevenuePredictionEngine:
    """Predicts revenue for niches, affiliates, and platforms using historical data."""
    _instance: Optional["RevenuePredictionEngine"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "RevenuePredictionEngine":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._niche_predictions: Dict[str, NicheRevenuePrediction] = {}
        self._affiliate_predictions: Dict[str, AffiliatePrediction] = {}
        self._platform_predictions: Dict[str, PlatformPrediction] = {}
        self._prediction_history: List[Dict[str, Any]] = []

    def predict_niche_revenue(self, niche: str, monthly_traffic: int,
                              avg_cpc: float, conversion_rate: float,
                              avg_commission: float, best_affiliate: str = "",
                              best_platform: str = "") -> NicheRevenuePrediction:
        p = NicheRevenuePrediction(niche)
        clicks = monthly_traffic * 0.03
        conversions = clicks * (conversion_rate / 100)
        p.predicted_monthly_revenue = conversions * avg_commission
        p.predicted_annual_revenue = p.predicted_monthly_revenue * 12
        p.best_affiliate = best_affiliate
        p.best_platform = best_platform
        p.factors = {
            "traffic": monthly_traffic, "cpc": avg_cpc,
            "conversion_rate": conversion_rate, "avg_commission": avg_commission,
        }
        p.confidence = min(monthly_traffic / 100000, 1.0) * 70 + 20
        p.low_estimate = p.predicted_monthly_revenue * 0.4
        p.high_estimate = p.predicted_monthly_revenue * 2.0
        self._niche_predictions[niche] = p
        return p

    def predict_affiliate_revenue(self, affiliate: str, niche: str,
                                   conversion_rate: float, avg_commission: float,
                                   monthly_clicks: int) -> AffiliatePrediction:
        p = AffiliatePrediction(affiliate, niche)
        p.conversion_rate = conversion_rate
        p.avg_commission = avg_commission
        p.monthly_clicks_predicted = monthly_clicks
        p.epc = avg_commission * (conversion_rate / 100)
        p.monthly_revenue_predicted = p.epc * monthly_clicks
        p.confidence = min(monthly_clicks / 5000, 1.0) * 60 + 25
        p.data_points = 1
        key = f"{affiliate}_{niche}"
        self._affiliate_predictions[key] = p
        return p

    def predict_platform_revenue(self, platform: str, niche: str,
                                  avg_reach: int, engagement_rate: float,
                                  affiliate_click_rate: float,
                                  monthly_content: int,
                                  revenue_per_click: float = 0.50) -> PlatformPrediction:
        p = PlatformPrediction(platform, niche)
        p.avg_reach = avg_reach
        p.avg_engagement_rate = engagement_rate
        p.affiliate_click_rate = affiliate_click_rate
        p.monthly_content_count = monthly_content
        total_clicks = avg_reach * (engagement_rate / 100) * (affiliate_click_rate / 100) * monthly_content
        p.predicted_monthly_revenue = total_clicks * revenue_per_click
        p.roi_per_post = p.predicted_monthly_revenue / monthly_content if monthly_content > 0 else 0
        p.confidence = min(avg_reach / 50000, 1.0) * 50 + 30
        key = f"{platform}_{niche}"
        self._platform_predictions[key] = p
        return p

    def get_niche_prediction(self, niche: str) -> Optional[NicheRevenuePrediction]:
        return self._niche_predictions.get(niche)

    def get_all_niche_predictions(self) -> List[NicheRevenuePrediction]:
        return sorted(
            self._niche_predictions.values(),
            key=lambda p: p.predicted_monthly_revenue, reverse=True,
        )

    def get_affiliate_prediction(self, affiliate: str, niche: str = "") -> Optional[AffiliatePrediction]:
        key = f"{affiliate}_{niche}"
        return self._affiliate_predictions.get(key)

    def get_best_affiliates(self, niche: str = "") -> List[AffiliatePrediction]:
        preds = list(self._affiliate_predictions.values())
        if niche:
            preds = [p for p in preds if p.niche == niche]
        return sorted(preds, key=lambda p: p.monthly_revenue_predicted, reverse=True)

    def get_platform_predictions(self, niche: str = "") -> List[PlatformPrediction]:
        preds = list(self._platform_predictions.values())
        if niche:
            preds = [p for p in preds if p.niche == niche]
        return sorted(preds, key=lambda p: p.predicted_monthly_revenue, reverse=True)

    def get_total_predicted_revenue(self) -> Dict[str, float]:
        niche_total = sum(p.predicted_monthly_revenue for p in self._niche_predictions.values())
        return {
            "monthly": round(niche_total, 2),
            "annual": round(niche_total * 12, 2),
            "niches_count": len(self._niche_predictions),
        }

    def get_prediction_report(self) -> Dict[str, Any]:
        total = self.get_total_predicted_revenue()
        return {
            "total_predicted_monthly": total["monthly"],
            "total_predicted_annual": total["annual"],
            "niche_predictions": {n: p.to_dict() for n, p in self._niche_predictions.items()},
            "affiliate_predictions_count": len(self._affiliate_predictions),
            "platform_predictions_count": len(self._platform_predictions),
            "top_niches": [p.to_dict() for p in self.get_all_niche_predictions()[:5]],
            "top_affiliates": [p.to_dict() for p in self.get_best_affiliates()[:5]],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "niche_predictions": len(self._niche_predictions),
            "affiliate_predictions": len(self._affiliate_predictions),
            "platform_predictions": len(self._platform_predictions),
        }


def get_revenue_prediction_engine() -> RevenuePredictionEngine:
    return RevenuePredictionEngine()
