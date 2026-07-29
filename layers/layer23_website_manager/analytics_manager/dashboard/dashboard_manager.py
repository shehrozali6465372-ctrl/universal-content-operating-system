"""DashboardManager — Display live KPIs, traffic, revenue, top pins, top boards, top articles."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class DashboardManager:
    def generate_dashboard(self, summary: Dict[str, Any], kpis: List[Any],
                            top_pins: List[Any], top_articles: List[Any],
                            insights: List[Any]) -> Dict[str, Any]:
        return {
            "summary": summary,
            "kpis": [k.to_dict() if hasattr(k, 'to_dict') else k for k in kpis],
            "top_pins": [p.to_dict() if hasattr(p, 'to_dict') else p for p in top_pins[:5]],
            "top_articles": [a.to_dict() if hasattr(a, 'to_dict') else a for a in top_articles[:5]],
            "insights": [i.to_dict() if hasattr(i, 'to_dict') else i for i in insights[:5]],
            "generated_at": time.time(),
        }

    def get_stats(self) -> Dict[str, int]:
        return {"total_dashboards": 1}
