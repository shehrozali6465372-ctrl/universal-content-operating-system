"""AnalyticsAPI — Provide analytics data to Revenue Manager, Learning Connector, Universal Dashboard."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class AnalyticsAPI:
    def __init__(self, parent):
        self._parent = parent

    def get_summary(self) -> Dict[str, Any]:
        return {
            "website": self._parent.website.get_summary(),
            "pinterest": self._parent.pinterest.get_summary(),
            "seo": self._parent.seo.get_summary(),
            "affiliate": self._parent.affiliate.get_summary(),
            "content": self._parent.content.get_summary(),
            "campaigns": self._parent.campaigns.get_summary(),
            "kpis": self._parent.kpi.get_summary(),
        }

    def get_top_performers(self, top_k: int = 5) -> Dict[str, Any]:
        return {
            "top_pins": [p.to_dict() for p in self._parent.pinterest.get_top_pins(top_k)],
            "top_articles": [a.to_dict() for a in self._parent.content.get_best_articles(top_k)],
            "top_products": [p.to_dict() for p in self._parent.affiliate.get_top_products(top_k)],
            "top_campaigns": [c.to_dict() for c in self._parent.campaigns.get_best_campaigns(top_k)],
        }

    def get_insights(self) -> List[Dict[str, Any]]:
        return [i.to_dict() for i in self._parent.insights._insights]

    def get_stats(self) -> Dict[str, int]:
        return {"total_queries": 1}
