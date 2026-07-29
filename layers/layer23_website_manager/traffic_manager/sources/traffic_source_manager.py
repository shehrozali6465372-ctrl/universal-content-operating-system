"""TrafficSourceManager — Track and manage all traffic sources: Pinterest, Google, Direct, Referral, Social."""
from __future__ import annotations
import time
import threading
import random
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.traffic_manager.models.traffic_models import TrafficSource, TrafficSourceType
from layers.layer23_website_manager.traffic_manager.exceptions import SourceNotFoundError


class TrafficSourceManager:
    """Track, categorize, and analyze traffic from all sources."""

    SOURCE_NAMES = {e.value: e.value.replace("_", " ").title() for e in TrafficSourceType}

    def __init__(self) -> None:
        self._sources: List[TrafficSource] = []
        self._lock = threading.Lock()

    def record_source(self, source_type: TrafficSourceType, visitor_id: str = "",
                       article_id: str = "", pin_id: str = "", board_id: str = "",
                       medium: str = "", campaign: str = "",
                       country: str = "", device: str = "desktop") -> TrafficSource:
        source = TrafficSource(
            visitor_id=visitor_id, source_type=source_type, medium=medium,
            campaign=campaign, article_id=article_id, pin_id=pin_id,
            board_id=board_id, country=country, device=device,
        )
        with self._lock:
            self._sources.append(source)
        return source

    def get_sources(self, days: int = 30, source_type: Optional[TrafficSourceType] = None) -> List[TrafficSource]:
        cutoff = time.time() - (days * 86400)
        result = [s for s in self._sources if s.created_at >= cutoff]
        if source_type:
            result = [s for s in result if s.source_type == source_type]
        return result

    def get_traffic_breakdown(self, days: int = 30) -> Dict[str, int]:
        sources = self.get_sources(days)
        breakdown: Dict[str, int] = {}
        for s in sources:
            name = self.SOURCE_NAMES.get(s.source_type.value, s.source_type.value)
            breakdown[name] = breakdown.get(name, 0) + 1
        return dict(sorted(breakdown.items(), key=lambda x: x[1], reverse=True))

    def simulate_traffic(self, article_id: str, pin_id: str = "", board_id: str = "",
                          total_visits: int = 100) -> int:
        sources = [TrafficSourceType.PINTEREST, TrafficSourceType.GOOGLE_ORGANIC,
                    TrafficSourceType.DIRECT, TrafficSourceType.REFERRAL, TrafficSourceType.SOCIAL]
        devices = ["desktop", "mobile", "tablet"]
        countries = ["US", "UK", "CA", "AU", "IN", "DE", "FR"]
        count = 0
        for _ in range(total_visits):
            st = random.choice(sources)
            self.record_source(st, article_id=article_id, pin_id=pin_id, board_id=board_id,
                                device=random.choice(devices), country=random.choice(countries))
            count += 1
        return count

    def get_stats(self) -> Dict[str, Any]:
        return {"total_sources": len(self._sources), "unique_sources": len(set(s.source_type.value for s in self._sources))}
