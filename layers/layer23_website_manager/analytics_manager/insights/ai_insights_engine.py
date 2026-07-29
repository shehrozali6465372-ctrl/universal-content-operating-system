"""AIInsightsEngine — Automatically generate actionable insights from analytics data."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.analytics_manager.models.analytics_models import AIInsight, InsightType


class AIInsightsEngine:
    def __init__(self):
        self._insights: List[AIInsight] = []

    def generate_insights(self, traffic_breakdown: Dict[str, int] = None,
                           top_pins: List[Any] = None,
                           top_articles: List[Any] = None,
                           affiliate_summary: Dict[str, Any] = None,
                           content_summary: Dict[str, Any] = None) -> List[AIInsight]:
        insights = []

        # Pinterest traffic insight
        if traffic_breakdown:
            pinterest_pct = (traffic_breakdown.get("Pinterest", 0) / max(sum(traffic_breakdown.values()), 1)) * 100
            if pinterest_pct > 50:
                insights.append(AIInsight(insight_type=InsightType.POSITIVE, title="Strong Pinterest Traffic",
                    message=f"Pinterest drives {pinterest_pct:.0f}% of total traffic",
                    category="traffic", metric_value=pinterest_pct,
                    recommendation="Double down on Pinterest content strategy"))
            elif pinterest_pct < 20:
                insights.append(AIInsight(insight_type=InsightType.WARNING, title="Low Pinterest Traffic",
                    message=f"Only {pinterest_pct:.0f}% traffic from Pinterest",
                    category="traffic", metric_value=pinterest_pct,
                    recommendation="Optimize pins for better reach"))

        # Affiliate insight
        if affiliate_summary:
            cr = affiliate_summary.get("conversion_rate", 0)
            if cr < 1:
                insights.append(AIInsight(insight_type=InsightType.NEGATIVE, title="Low Affiliate Conversion",
                    message=f"Conversion rate only {cr}%", category="revenue",
                    metric_value=cr, recommendation="Improve product targeting and CTAs"))
            elif cr > 5:
                insights.append(AIInsight(insight_type=InsightType.POSITIVE, title="High Affiliate Conversion",
                    message=f"Conversion rate at {cr}%", category="revenue",
                    metric_value=cr, recommendation="Scale successful affiliate strategies"))

        # Content insight
        if content_summary:
            evergreen = content_summary.get("evergreen", 0)
            if evergreen > 0:
                insights.append(AIInsight(insight_type=InsightType.OPPORTUNITY, title="Evergreen Content Assets",
                    message=f"{evergreen} evergreen articles generating passive traffic",
                    category="content", metric_value=evergreen,
                    recommendation="Create more pillar content in top-performing niches"))

        self._insights.extend(insights)
        return insights

    def get_stats(self) -> Dict[str, int]:
        return {"total_insights": len(self._insights)}
