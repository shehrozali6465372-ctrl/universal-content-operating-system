"""AIMonetizationOptimizer — AI-driven monetization strategy optimization."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional, Tuple


class NichePerformance:
    __slots__ = ("niche", "total_clicks", "total_conversions", "total_revenue",
                 "total_posts", "avg_epc", "avg_ctr", "trend", "score",
                 "recommendations")

    def __init__(self, niche: str) -> None:
        self.niche = niche
        self.total_clicks = 0
        self.total_conversions = 0
        self.total_revenue = 0.0
        self.total_posts = 0
        self.avg_epc = 0.0
        self.avg_ctr = 0.0
        self.trend = "stable"
        self.score = 0.0
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "niche": self.niche,
            "total_clicks": self.total_clicks,
            "total_conversions": self.total_conversions,
            "total_revenue": round(self.total_revenue, 2),
            "total_posts": self.total_posts,
            "avg_epc": round(self.avg_epc, 4),
            "avg_ctr": round(self.avg_ctr, 2),
            "trend": self.trend,
            "score": round(self.score, 2),
            "recommendations": self.recommendations,
        }


class StrategyRecommendation:
    __slots__ = ("id", "type", "niche", "action", "priority", "expected_impact",
                 "reason", "created_at", "status")

    def __init__(self, rec_type: str, niche: str, action: str,
                 priority: int = 5, expected_impact: float = 0.0, reason: str = "") -> None:
        self.id = f"rec_{int(time.time() * 1000)}"
        self.type = rec_type
        self.niche = niche
        self.action = action
        self.priority = priority
        self.expected_impact = expected_impact
        self.reason = reason
        self.created_at = time.time()
        self.status = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "type": self.type, "niche": self.niche,
            "action": self.action, "priority": self.priority,
            "expected_impact": round(self.expected_impact, 2),
            "reason": self.reason, "status": self.status,
        }


class ContentScore:
    __slots__ = ("post_id", "title", "niche", "clicks", "conversions", "revenue",
                 "ctr", "conversion_rate", "epc", "overall_score", "category")

    def __init__(self, post_id: str, title: str = "", niche: str = "") -> None:
        self.post_id = post_id
        self.title = title
        self.niche = niche
        self.clicks = 0
        self.conversions = 0
        self.revenue = 0.0
        self.ctr = 0.0
        self.conversion_rate = 0.0
        self.epc = 0.0
        self.overall_score = 0.0
        self.category = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "post_id": self.post_id, "title": self.title, "niche": self.niche,
            "clicks": self.clicks, "conversions": self.conversions,
            "revenue": round(self.revenue, 2),
            "ctr": round(self.ctr, 2), "conversion_rate": round(self.conversion_rate, 2),
            "epc": round(self.epc, 4), "overall_score": round(self.overall_score, 2),
            "category": self.category,
        }


class AIMonetizationOptimizer:
    """AI-driven system that analyzes performance and recommends optimization strategies."""
    _instance: Optional["AIMonetizationOptimizer"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "AIMonetizationOptimizer":
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
        self._niche_perf: Dict[str, NichePerformance] = {}
        self._content_scores: Dict[str, ContentScore] = {}
        self._recommendations: List[StrategyRecommendation] = []
        self._optimization_history: List[Dict[str, Any]] = []

    def record_niche_data(self, niche: str, clicks: int, conversions: int,
                          revenue: float, posts: int) -> NichePerformance:
        if niche not in self._niche_perf:
            self._niche_perf[niche] = NichePerformance(niche)
        np = self._niche_perf[niche]
        np.total_clicks += clicks
        np.total_conversions += conversions
        np.total_revenue += revenue
        np.total_posts += posts
        np.avg_epc = (np.total_revenue / np.total_clicks) if np.total_clicks > 0 else 0
        np.avg_ctr = 0.0
        return np

    def score_content(self, post_id: str, title: str, niche: str,
                      clicks: int, impressions: int, conversions: int,
                      revenue: float) -> ContentScore:
        cs = ContentScore(post_id, title, niche)
        cs.clicks = clicks
        cs.conversions = conversions
        cs.revenue = revenue
        cs.ctr = (clicks / impressions * 100) if impressions > 0 else 0
        cs.conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
        cs.epc = (revenue / clicks) if clicks > 0 else 0

        ctr_score = min(cs.ctr / 5.0, 1.0) * 25
        cr_score = min(cs.conversion_rate / 10.0, 1.0) * 35
        epc_score = min(cs.epc / 1.0, 1.0) * 40
        cs.overall_score = ctr_score + cr_score + epc_score

        if cs.overall_score >= 70:
            cs.category = "star"
        elif cs.overall_score >= 40:
            cs.category = "performer"
        elif cs.overall_score >= 15:
            cs.category = "average"
        else:
            cs.category = "underperformer"

        self._content_scores[post_id] = cs
        return cs

    def analyze_niches(self) -> List[NichePerformance]:
        niches = list(self._niche_perf.values())
        for np in niches:
            np.score = self._calculate_niche_score(np)
            np.recommendations = self._generate_niche_recommendations(np)
            if np.score >= 70:
                np.trend = "growing"
            elif np.score >= 40:
                np.trend = "stable"
            else:
                np.trend = "declining"
        niches.sort(key=lambda n: n.score, reverse=True)
        return niches

    def _calculate_niche_score(self, np: NichePerformance) -> float:
        if np.total_clicks == 0:
            return 0.0
        epc_score = min(np.avg_epc / 0.5, 1.0) * 30
        conversion_score = min(
            (np.total_conversions / np.total_clicks) / 0.1, 1.0
        ) * 35
        revenue_score = min(np.total_revenue / 1000, 1.0) * 20
        volume_score = min(np.total_posts / 50, 1.0) * 15
        return epc_score + conversion_score + revenue_score + volume_score

    def _generate_niche_recommendations(self, np: NichePerformance) -> List[str]:
        recs = []
        if np.avg_epc < 0.05:
            recs.append("EPC bahut kam hai — higher commission programs dhundhein")
        if np.total_clicks > 0 and (np.total_conversions / np.total_clicks) < 0.02:
            recs.append("Conversion rate kam hai — landing pages optimize karein")
        if np.total_posts < 10:
            recs.append("Content volume kam hai — zyada posts publish karein")
        if np.score >= 70:
            recs.append("⭐ High performer — is niche mein budget barhayein")
        if np.total_revenue > 500:
            recs.append("Revenue strong hai — premium affiliate programs join karein")
        if not recs:
            recs.append("Performance theek hai — consistency banaye rakhein")
        return recs

    def generate_recommendations(self) -> List[StrategyRecommendation]:
        self._recommendations.clear()
        niches = self.analyze_niches()

        for np in niches:
            if np.score < 30:
                self._recommendations.append(StrategyRecommendation(
                    "optimization", np.niche,
                    f"{np.niche} niche mein performance low hai — content quality improve karein",
                    priority=8, expected_impact=20.0,
                    reason=f"Score: {np.score:.1f}, EPC: {np.avg_epc:.4f}",
                ))
            elif np.score >= 70:
                self._recommendations.append(StrategyRecommendation(
                    "scale", np.niche,
                    f"{np.niche} mein budget aur content barhayein",
                    priority=3, expected_impact=40.0,
                    reason=f"Score: {np.score:.1f}, Revenue: ${np.total_revenue:.2f}",
                ))

        top_content = sorted(
            self._content_scores.values(),
            key=lambda c: c.overall_score, reverse=True,
        )[:5]
        for cs in top_content:
            if cs.category == "star":
                self._recommendations.append(StrategyRecommendation(
                    "replicate", cs.niche,
                    f"'{cs.title}' type ka content aur banayein (Score: {cs.overall_score:.1f})",
                    priority=4, expected_impact=25.0,
                    reason=f"Star performer: EPC={cs.epc:.4f}, CR={cs.conversion_rate:.1f}%",
                ))

        underperformers = [
            cs for cs in self._content_scores.values() if cs.category == "underperformer"
        ]
        if underperformers:
            self._recommendations.append(StrategyRecommendation(
                "audit", "all",
                f"{len(underperformers)} underperforming posts hain — links aur CTAs check karein",
                priority=6, expected_impact=15.0,
                reason="Low scores detected across multiple posts",
            ))

        self._recommendations.sort(key=lambda r: r.priority, reverse=True)
        return self._recommendations

    def get_optimization_report(self) -> Dict[str, Any]:
        niches = self.analyze_niches()
        recs = self.generate_recommendations()
        all_content = list(self._content_scores.values())
        stars = sum(1 for c in all_content if c.category == "star")
        performers = sum(1 for c in all_content if c.category == "performer")
        avg = sum(1 for c in all_content if c.category == "average")
        under = sum(1 for c in all_content if c.category == "underperformer")
        return {
            "total_niches": len(niches),
            "total_content_scored": len(all_content),
            "niche_breakdown": {n.niche: n.to_dict() for n in niches},
            "content_categories": {
                "star": stars, "performer": performers,
                "average": avg, "underperformer": under,
            },
            "recommendations": [r.to_dict() for r in recs],
            "total_recommendations": len(recs),
            "top_niches": [n.niche for n in niches[:3]],
        }

    def get_top_content(self, limit: int = 10) -> List[ContentScore]:
        return sorted(
            self._content_scores.values(),
            key=lambda c: c.overall_score, reverse=True,
        )[:limit]

    def stats(self) -> Dict[str, Any]:
        return {
            "niches": len(self._niche_perf),
            "content_scored": len(self._content_scores),
            "recommendations": len(self._recommendations),
            "history": len(self._optimization_history),
        }


def get_monetization_optimizer() -> AIMonetizationOptimizer:
    return AIMonetizationOptimizer()
