"""Source Ranker - Ranks intelligence sources by reliability and relevance."""
from __future__ import annotations
from typing import Dict, List


class SourceScore:
    __slots__ = ("name", "reliability", "relevance", "freshness", "overall")
    def __init__(self, name: str = "") -> None:
        self.name = name
        self.reliability = 0.5
        self.relevance = 0.5
        self.freshness = 0.5
        self.overall = 0.5
    def to_dict(self) -> Dict:
        return {"name": self.name, "reliability": round(self.reliability, 3),
                "relevance": round(self.relevance, 3), "freshness": round(self.freshness, 3),
                "overall": round(self.overall, 3)}


class SourceRanker:
    def __init__(self, weights: Dict[str, float] = None) -> None:
        self._weights = weights or {"reliability": 0.4, "relevance": 0.35, "freshness": 0.25}

    def rank(self, sources: Dict[str, Dict[str, float]]) -> List[SourceScore]:
        scores = []
        for name, metrics in sources.items():
            ss = SourceScore(name)
            ss.reliability = metrics.get("reliability", 0.5)
            ss.relevance = metrics.get("relevance", 0.5)
            ss.freshness = metrics.get("freshness", 0.5)
            ss.overall = (ss.reliability * self._weights["reliability"] +
                         ss.relevance * self._weights["relevance"] +
                         ss.freshness * self._weights["freshness"])
            scores.append(ss)
        scores.sort(key=lambda s: s.overall, reverse=True)
        return scores
