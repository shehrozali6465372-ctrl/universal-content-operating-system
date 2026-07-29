"""VisitorTracker — Track visitors, sessions, new vs returning, page views, duration."""
from __future__ import annotations
import time
import threading
import uuid
import random
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.traffic_manager.models.traffic_models import Visitor
from layers.layer23_website_manager.traffic_manager.exceptions import VisitorTrackingError


class VisitorTracker:
    """Track and analyze visitor sessions, behavior, and engagement."""

    def __init__(self) -> None:
        self._visitors: Dict[str, List[Visitor]] = {}
        self._lock = threading.Lock()

    def record_visit(self, visitor_id: str = "", is_new: bool = True,
                      device: str = "desktop", country: str = "") -> Visitor:
        visitor = Visitor(visitor_id=visitor_id or str(uuid.uuid4())[:12], is_new=is_new,
                           device=device, country=country)
        with self._lock:
            if visitor.visitor_id not in self._visitors:
                self._visitors[visitor.visitor_id] = []
            self._visitors[visitor.visitor_id].append(visitor)
        return visitor

    def get_visitor_count(self, days: int = 30) -> Dict[str, int]:
        cutoff = time.time() - (days * 86400)
        total = new = returning = 0
        for vlist in self._visitors.values():
            for v in vlist:
                if v.first_visit >= cutoff:
                    total += 1
                    if v.is_new: new += 1
                    else: returning += 1
        return {"total": total, "new": new, "returning": returning, "new_rate": round(new / max(total, 1) * 100, 1)}

    def simulate_visitors(self, count: int = 50) -> int:
        devices = ["desktop", "mobile", "tablet"]
        countries = ["US", "UK", "CA", "AU", "IN"]
        for i in range(count):
            vid = f"v_{i}_{int(time.time())}"
            self.record_visit(vid, is_new=random.random() > 0.3,
                               device=random.choice(devices), country=random.choice(countries))
        return count

    def get_stats(self) -> Dict[str, Any]:
        total = sum(len(v) for v in self._visitors.values())
        unique = len(self._visitors)
        return {"total_visits": total, "unique_visitors": unique}
