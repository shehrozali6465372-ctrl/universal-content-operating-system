"""RiskManager — Detect and manage execution risks."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_RM_COUNTER = itertools.count(1)

RISK_LEVELS = ("low", "medium", "high", "critical")


class Risk:
    """An identified risk."""

    __slots__ = ("risk_id", "category", "description", "level",
                 "probability", "impact", "mitigation", "detected_at")

    def __init__(self, category: str = "", description: str = "") -> None:
        self.risk_id: str = f"risk_{next(_RM_COUNTER)}"
        self.category = category
        self.description = description
        self.level: str = "medium"
        self.probability: float = 0.5
        self.impact: float = 0.5
        self.mitigation: str = ""
        self.detected_at: float = time.time()

    @property
    def risk_score(self) -> float:
        return round(self.probability * self.impact, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_id": self.risk_id, "category": self.category,
            "level": self.level, "risk_score": self.risk_score,
        }


class RiskManager:
    """Detect, assess, and mitigate execution risks."""

    def __init__(self) -> None:
        self._risks: List[Risk] = []
        self._mitigations: List[Dict[str, Any]] = []

    def detect_risks(self, layers: List[str], context: Optional[Dict[str, Any]] = None) -> List[Risk]:
        detected = []
        for layer in layers:
            if "publishing" in layer:
                risk = Risk("platform", f"Platform policy risk for {layer}")
                risk.level = "medium"
                risk.probability = 0.3
                risk.mitigation = "Check platform policies before publishing"
                self._risks.append(risk)
                detected.append(risk)
            if "image" in layer:
                risk = Risk("resource", f"GPU/resource risk for {layer}")
                risk.level = "low"
                risk.probability = 0.2
                risk.mitigation = "Ensure GPU availability"
                self._risks.append(risk)
                detected.append(risk)
            if "learning" in layer:
                risk = Risk("quality", f"Learning accuracy risk for {layer}")
                risk.level = "medium"
                risk.probability = 0.4
                risk.mitigation = "Validate learning outputs"
                self._risks.append(risk)
                detected.append(risk)
        return detected

    def assess_risk(self, risk: Risk) -> Dict[str, Any]:
        return {
            "risk_id": risk.risk_id, "level": risk.level,
            "score": risk.risk_score, "needs_mitigation": risk.risk_score > 0.3,
        }

    def suggest_rollback(self, risks: List[Risk]) -> bool:
        critical = [r for r in risks if r.level == "critical" or r.risk_score > 0.6]
        return len(critical) > 0

    def get_all_risks(self) -> List[Risk]:
        return list(self._risks)

    def get_high_risks(self) -> List[Risk]:
        return [r for r in self._risks if r.level in ("high", "critical")]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_risks": len(self._risks),
                "high_risks": len(self.get_high_risks())}
