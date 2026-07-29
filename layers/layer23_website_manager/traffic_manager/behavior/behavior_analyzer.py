"""BehaviorAnalyzer — Analyze scroll depth, time on page, click maps, user journeys."""
from __future__ import annotations
import time
import threading
import random
from typing import Any, Dict, List, Optional


class BehaviorAnalyzer:
    """Analyze user behavior — scroll depth, time on page, engagement patterns."""

    def __init__(self) -> None:
        self._behaviors: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def record_behavior(self, article_id: str, scroll_depth: float = 0.0,
                         time_on_page: float = 0.0, device: str = "desktop",
                         bounced: bool = False) -> Dict[str, Any]:
        record = {"article_id": article_id, "scroll_depth": scroll_depth,
                   "time_on_page": time_on_page, "device": device, "bounced": bounced,
                   "timestamp": time.time()}
        with self._lock: self._behaviors.append(record)
        return record

    def get_article_behavior(self, article_id: str) -> Dict[str, Any]:
        records = [b for b in self._behaviors if b["article_id"] == article_id]
        if not records: return {}
        avg_scroll = sum(r["scroll_depth"] for r in records) / len(records)
        avg_time = sum(r["time_on_page"] for r in records) / len(records)
        bounce_rate = sum(1 for r in records if r["bounced"]) / len(records) * 100
        return {"article_id": article_id, "sessions": len(records),
                "avg_scroll_depth": round(avg_scroll, 1),
                "avg_time_on_page": round(avg_time, 1),
                "bounce_rate": round(bounce_rate, 1)}

    def simulate_behavior(self, article_count: int = 3, sessions: int = 30) -> int:
        for _ in range(sessions):
            aid = f"art_{random.randint(0, article_count - 1)}"
            self.record_behavior(aid, scroll_depth=random.uniform(10, 100),
                                  time_on_page=random.uniform(10, 300),
                                  device=random.choice(["desktop", "mobile"]),
                                  bounced=random.random() < 0.3)
        return sessions

    def get_stats(self) -> Dict[str, Any]:
        return {"total_records": len(self._behaviors)}
