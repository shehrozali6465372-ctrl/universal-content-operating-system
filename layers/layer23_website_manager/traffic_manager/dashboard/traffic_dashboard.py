"""TrafficDashboard — Live traffic overview: sources, top content, daily growth."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class TrafficDashboard:
    """Generate live traffic dashboard with sources, top content, and growth metrics."""

    def generate(self, total_visitors: int, source_breakdown: Dict[str, int],
                  top_pages: List[Any], top_pins: List[Any],
                  total_articles: int, health_score: float) -> Dict[str, Any]:
        """Generate complete traffic dashboard."""
        return {
            "live": {"active_visitors": total_visitors, "sources": source_breakdown},
            "content": {"top_pages": [{"title": p.title[:40] if hasattr(p, 'title') else str(p), "sessions": p.sessions if hasattr(p, 'sessions') else 0} for p in top_pages[:5]],
                        "top_pins": [{"pin_id": p[0], "clicks": p[1]} for p in top_pins[:5]],
                        "total_articles": total_articles},
            "health": {"score": round(health_score, 1)},
            "generated_at": time.time(),
        }

    def get_stats(self) -> Dict[str, int]:
        return {"total_dashboards": 1}
