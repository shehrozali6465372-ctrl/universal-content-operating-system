"""SearchTrafficManager — Track organic keywords, search position, CTR, indexed pages."""
from __future__ import annotations
import time
import threading
import random
from typing import Any, Dict, List, Optional


class SearchTrafficManager:
    """Track and analyze search engine traffic — keywords, positions, CTR."""

    def __init__(self) -> None:
        self._keywords: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def record_keyword(self, keyword: str, position: float = 10.0,
                        clicks: int = 1, impressions: int = 100,
                        article_id: str = "") -> None:
        with self._lock:
            if keyword not in self._keywords:
                self._keywords[keyword] = {"clicks": 0, "impressions": 0,
                    "positions": [], "article_ids": set()}
            kw = self._keywords[keyword]
            kw["clicks"] += clicks
            kw["impressions"] += impressions
            kw["positions"].append(position)
            kw["article_ids"].add(article_id)

    def get_keyword_stats(self, keyword: str) -> Dict[str, Any]:
        kw = self._keywords.get(keyword)
        if not kw: return {}
        avg_pos = sum(kw["positions"]) / max(len(kw["positions"]), 1)
        return {"keyword": keyword, "clicks": kw["clicks"], "impressions": kw["impressions"],
                "ctr": round(kw["clicks"] / max(kw["impressions"], 1) * 100, 2),
                "avg_position": round(avg_pos, 1), "articles": len(kw["article_ids"])}

    def get_top_keywords(self, top_k: int = 5) -> List[Dict[str, Any]]:
        results = []
        for kw, data in self._keywords.items():
            avg_pos = sum(data["positions"]) / max(len(data["positions"]), 1)
            results.append({"keyword": kw, "clicks": data["clicks"],
                "ctr": round(data["clicks"] / max(data["impressions"], 1) * 100, 2),
                "avg_position": round(avg_pos, 1)})
        return sorted(results, key=lambda x: x["clicks"], reverse=True)[:top_k]

    def simulate_search(self, keyword_count: int = 5) -> int:
        kw_list = ["bedroom ideas", "home decor", "fashion trends", "beauty tips", "tech reviews",
                    "fitness guide", "travel tips", "money saving", "DIY crafts"]
        for i in range(min(keyword_count, len(kw_list))):
            self.record_keyword(kw_list[i], position=random.uniform(1, 20),
                                 clicks=random.randint(5, 200), impressions=random.randint(100, 5000))
        return keyword_count

    def get_stats(self) -> Dict[str, Any]:
        return {"total_keywords": len(self._keywords),
                "total_clicks": sum(d["clicks"] for d in self._keywords.values()),
                "total_impressions": sum(d["impressions"] for d in self._keywords.values())}
