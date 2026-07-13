"""
Decision Trace Engine
Layer 2: Research Engine — Module 7

Records complete decision traces for every research decision:
- Full trace with scores from each module
- Confidence tracking
- Reason recording
- Historical analysis
- Pattern detection
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


class DecisionTrace:
    """A complete trace of a research decision."""

    __slots__ = (
        "trace_id", "topic", "decision",
        "trend_score", "topic_score", "competitor_score",
        "audience_score", "knowledge_score", "verification_score",
        "overall_confidence", "risk_level",
        "reasons", "evidence", "module_scores",
        "outcome", "performance_score",
        "created_at", "updated_at",
    )

    def __init__(
        self,
        topic: str,
        decision: str = "",
        trend_score: float = 0.0,
        topic_score: float = 0.0,
        competitor_score: float = 0.0,
        audience_score: float = 0.0,
        knowledge_score: float = 0.0,
        verification_score: float = 0.0,
        overall_confidence: float = 0.0,
        risk_level: str = "MEDIUM",
        reasons: Optional[List[str]] = None,
        evidence: Optional[List[str]] = None,
    ):
        self.trace_id = f"trace_{int(datetime.now(timezone.utc).timestamp())}_{hash(topic) % 100000}"
        self.topic = topic
        self.decision = decision
        self.trend_score = max(0.0, min(10.0, trend_score))
        self.topic_score = max(0.0, min(10.0, topic_score))
        self.competitor_score = max(0.0, min(10.0, competitor_score))
        self.audience_score = max(0.0, min(10.0, audience_score))
        self.knowledge_score = max(0.0, min(10.0, knowledge_score))
        self.verification_score = max(0.0, min(10.0, verification_score))
        self.overall_confidence = max(0.0, min(1.0, overall_confidence))
        self.risk_level = risk_level
        self.reasons = reasons or []
        self.evidence = evidence or []
        self.module_scores = {
            "trend": self.trend_score,
            "topic": self.topic_score,
            "competitor": self.competitor_score,
            "audience": self.audience_score,
            "knowledge": self.knowledge_score,
            "verification": self.verification_score,
        }
        self.outcome = ""
        self.performance_score = 0.0
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at

    def update_outcome(self, outcome: str, performance_score: float):
        """Record the outcome of a decision."""
        self.outcome = outcome
        self.performance_score = max(0.0, min(10.0, performance_score))
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_weakest_module(self) -> Tuple[str, float]:
        """Find the module with the lowest score."""
        if not self.module_scores:
            return ("none", 0.0)
        weakest = min(self.module_scores, key=self.module_scores.get)
        return (weakest, self.module_scores[weakest])

    def get_strongest_module(self) -> Tuple[str, float]:
        """Find the module with the highest score."""
        if not self.module_scores:
            return ("none", 0.0)
        strongest = max(self.module_scores, key=self.module_scores.get)
        return (strongest, self.module_scores[strongest])

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id, "topic": self.topic,
            "decision": self.decision,
            "module_scores": self.module_scores,
            "overall_confidence": self.overall_confidence,
            "risk_level": self.risk_level,
            "reasons": self.reasons, "evidence": self.evidence,
            "outcome": self.outcome,
            "performance_score": self.performance_score,
            "weakest_module": self.get_weakest_module()[0],
            "strongest_module": self.get_strongest_module()[0],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DecisionTrace":
        ms = data.get("module_scores", {})
        t = cls(
            topic=data.get("topic", ""),
            decision=data.get("decision", ""),
            trend_score=ms.get("trend", 0),
            topic_score=ms.get("topic", 0),
            competitor_score=ms.get("competitor", 0),
            audience_score=ms.get("audience", 0),
            knowledge_score=ms.get("knowledge", 0),
            verification_score=ms.get("verification", 0),
            overall_confidence=data.get("overall_confidence", 0),
            risk_level=data.get("risk_level", "MEDIUM"),
            reasons=data.get("reasons", []),
            evidence=data.get("evidence", []),
        )
        t.trace_id = data.get("trace_id", t.trace_id)
        t.outcome = data.get("outcome", "")
        t.performance_score = data.get("performance_score", 0)
        t.created_at = data.get("created_at", t.created_at)
        t.updated_at = data.get("updated_at", t.updated_at)
        return t


class DecisionTraceEngine:
    """Records and analyzes decision traces."""

    def __init__(self):
        self._traces: Dict[str, DecisionTrace] = {}
        self._topic_traces: Dict[str, List[str]] = {}

    def record(self, trace: DecisionTrace) -> str:
        self._traces[trace.trace_id] = trace
        self._topic_traces.setdefault(trace.topic, []).append(trace.trace_id)
        return trace.trace_id

    def get(self, trace_id: str) -> Optional[DecisionTrace]:
        return self._traces.get(trace_id)

    def get_by_topic(self, topic: str) -> List[DecisionTrace]:
        tids = self._topic_traces.get(topic, [])
        return [self._traces[tid] for tid in tids if tid in self._traces]

    def get_recent(self, count: int = 10) -> List[DecisionTrace]:
        return sorted(self._traces.values(), key=lambda t: t.created_at, reverse=True)[:count]

    def get_successful(self) -> List[DecisionTrace]:
        return [t for t in self._traces.values() if t.outcome == "success"]

    def get_failed(self) -> List[DecisionTrace]:
        return [t for t in self._traces.values() if t.outcome == "failure"]

    def get_average_confidence(self) -> float:
        if not self._traces:
            return 0.0
        return round(sum(t.overall_confidence for t in self._traces.values()) / len(self._traces), 3)

    def get_average_performance(self) -> float:
        scored = [t for t in self._traces.values() if t.performance_score > 0]
        if not scored:
            return 0.0
        return round(sum(t.performance_score for t in scored) / len(scored), 3)

    def get_weakest_modules(self) -> Dict[str, float]:
        """Find which modules are consistently weakest."""
        module_totals: Dict[str, List[float]] = {}
        for trace in self._traces.values():
            for module, score in trace.module_scores.items():
                module_totals.setdefault(module, []).append(score)
        return {m: round(sum(s) / len(s), 2) for m, s in module_totals.items() if s}

    def get_successful_patterns(self) -> Dict[str, any]:
        """Analyze patterns in successful decisions."""
        successful = self.get_successful()
        if not successful:
            return {}
        avg_scores = {}
        modules = successful[0].module_scores.keys()
        for mod in modules:
            scores = [t.module_scores.get(mod, 0) for t in successful]
            avg_scores[mod] = round(sum(scores) / len(scores), 2)
        return {
            "count": len(successful),
            "avg_module_scores": avg_scores,
            "avg_confidence": round(sum(t.overall_confidence for t in successful) / len(successful), 3),
        }

    def size(self) -> int:
        return len(self._traces)

    def stats(self) -> dict:
        return {
            "total_traces": len(self._traces),
            "topics_covered": len(self._topic_traces),
            "avg_confidence": self.get_average_confidence(),
            "avg_performance": self.get_average_performance(),
            "successful": len(self.get_successful()),
            "failed": len(self.get_failed()),
        }
