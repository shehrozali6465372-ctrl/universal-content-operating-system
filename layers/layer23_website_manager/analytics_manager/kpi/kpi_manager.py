"""KPIManager — Calculate daily, weekly, monthly KPIs with growth % and success rate."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.analytics_manager.models.analytics_models import KPI, KPICategory


class KPIManager:
    def __init__(self):
        self._kpis: Dict[str, KPI] = {}
        self._lock = threading.Lock()
        self._history: List[Dict] = []

    def calculate_kpi(self, name: str, category: KPICategory, value: float,
                       previous_value: float = 0.0, unit: str = "") -> KPI:
        kpi = KPI(category=category, name=name, value=value, previous_value=previous_value, unit=unit)
        if previous_value > 0:
            if value > previous_value: kpi.trend = "up"
            elif value < previous_value: kpi.trend = "down"
        with self._lock:
            self._kpis[name] = kpi
            self._history.append({"name": name, "value": value, "timestamp": time.time()})
        return kpi

    def get_kpi(self, name: str) -> Optional[KPI]:
        return self._kpis.get(name)

    def get_all_kpis(self, category: Optional[KPICategory] = None) -> List[KPI]:
        kpis = list(self._kpis.values())
        if category: kpis = [k for k in kpis if k.category == category]
        return kpis

    def get_summary(self) -> Dict[str, Any]:
        kpis = list(self._kpis.values())
        if not kpis: return {}
        return {"total_kpis": len(kpis), "up_trend": sum(1 for k in kpis if k.trend == "up"),
                "down_trend": sum(1 for k in kpis if k.trend == "down"),
                "avg_growth": round(sum(k.change_pct for k in kpis) / len(kpis), 1)}

    def get_stats(self) -> Dict:
        s = self.get_summary(); return {"total_kpis": s.get("total_kpis", 0)}
