"""Fusion Engine - Combines knowledge from multiple intelligence sources."""
from __future__ import annotations
from typing import Any, Dict, List


class UnifiedIntelligence:
    """Unified intelligence object combining all sources."""
    __slots__ = ("topic", "sources", "confidence", "evidence", "contradictions",
                 "recommendation", "metadata", "overall_score")
    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.sources: Dict[str, Any] = {}
        self.confidence = 0.0
        self.evidence: List[str] = []
        self.contradictions: List[str] = []
        self.recommendation = ""
        self.metadata: Dict = {}
        self.overall_score = 0.0
    def add_source(self, name: str, data: Any) -> None:
        self.sources[name] = data
    def to_dict(self) -> Dict:
        source_summaries = {}
        for name, data in self.sources.items():
            if hasattr(data, "to_dict"):
                source_summaries[name] = data.to_dict()
            elif isinstance(data, dict):
                source_summaries[name] = data
            else:
                source_summaries[name] = str(data)[:200]
        return {
            "topic": self.topic, "sources": source_summaries,
            "confidence": round(self.confidence, 3), "overall_score": round(self.overall_score, 3),
            "evidence": list(self.evidence), "contradictions": list(self.contradictions),
            "recommendation": self.recommendation,
        }


class ConflictResolver:
    """Resolves conflicts between different intelligence sources."""
    def resolve(self, values: Dict[str, float]) -> Dict:
        if not values:
            return {"resolved": 0.0, "method": "none", "agreement": 0.0}
        mean_val = sum(values.values()) / len(values)
        if len(values) == 1:
            return {"resolved": mean_val, "method": "single", "agreement": 1.0}
        variance = sum((v - mean_val) ** 2 for v in values.values()) / len(values)
        agreement = max(0.0, 1.0 - variance ** 0.5)
        if agreement > 0.8:
            resolved = mean_val
            method = "average"
        else:
            resolved = sum(values.values()) / len(values)
            method = "weighted_average"
        return {"resolved": round(resolved, 3), "method": method, "agreement": round(agreement, 3)}


class FusionEngine:
    """Fuses knowledge from research, trend, audience, competitor, content, and learning modules."""
    def __init__(self) -> None:
        self.resolver = ConflictResolver()
        self._source_weights = {
            "research": 0.2, "trend": 0.2, "audience": 0.15,
            "competitor": 0.15, "content": 0.15, "learning": 0.15,
        }

    def fuse(self, topic: str, sources: Dict[str, Any]) -> UnifiedIntelligence:
        ui = UnifiedIntelligence(topic)
        for name, data in sources.items():
            ui.add_source(name, data)

        # Collect scores from each source
        scores: Dict[str, float] = {}
        for name, data in sources.items():
            if isinstance(data, dict):
                score = data.get("score", data.get("confidence", data.get("overall_score", 0.5)))
            elif hasattr(data, "to_dict"):
                d = data.to_dict()
                score = d.get("overall_score", d.get("score", d.get("confidence", 0.5)))
            else:
                score = 0.5
            scores[name] = float(score)

        # Resolve conflicts
        resolution = self.resolver.resolve(scores)
        ui.overall_score = resolution["resolved"]

        # Weighted confidence
        total_w = 0
        weighted_conf = 0
        for name, score in scores.items():
            w = self._source_weights.get(name, 0.1)
            weighted_conf += score * w
            total_w += w
        ui.confidence = weighted_conf / total_w if total_w > 0 else 0.5

        # Evidence
        for name, score in scores.items():
            if score > 0.7:
                ui.evidence.append(f"Strong signal from {name} ({score:.0%})")
            elif score < 0.3:
                ui.evidence.append(f"Weak signal from {name} ({score:.0%})")

        # Contradictions
        if len(scores) > 1:
            vals = list(scores.values())
            if max(vals) - min(vals) > 0.5:
                high = [k for k, v in scores.items() if v > 0.7]
                low = [k for k, v in scores.items() if v < 0.3]
                if high and low:
                    ui.contradictions.append(f"Contradiction: {high} say strong, {low} say weak")

        # Recommendation
        if ui.confidence >= 0.7 and not ui.contradictions:
            ui.recommendation = f"High confidence: proceed with '{topic}'"
        elif ui.contradictions:
            ui.recommendation = f"Conflicting signals for '{topic}' — investigate further"
        else:
            ui.recommendation = f"Moderate confidence for '{topic}' — gather more data"

        return ui

    def fuse_batch(self, topics: Dict[str, Dict[str, Any]]) -> List[UnifiedIntelligence]:
        return [self.fuse(topic, sources) for topic, sources in topics.items()]
