"""Strategy Generator — Dynamic strategy generation from intelligence inputs."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class GeneratedStrategy:
    """A dynamically generated strategy."""
    __slots__ = ("strategy_id", "name", "horizon", "goals", "tactics",
                 "content_mix", "post_schedule", "risk_level", "confidence",
                 "reasoning", "source_data", "timestamp")

    def __init__(self, name: str = "", horizon: str = "short") -> None:
        self.strategy_id = f"strat_{int(time.time()*1000) % 10000000}"
        self.name = name
        self.horizon = horizon  # short, medium, long
        self.goals: List[Dict[str, Any]] = []
        self.tactics: List[Dict[str, Any]] = []
        self.content_mix: Dict[str, float] = {}  # type -> percentage
        self.post_schedule: List[Dict[str, Any]] = []
        self.risk_level = "medium"
        self.confidence = 0.0
        self.reasoning: List[str] = []
        self.source_data: Dict[str, Any] = {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "horizon": self.horizon,
            "goals": self.goals,
            "tactics": self.tactics,
            "content_mix": self.content_mix,
            "post_schedule": self.post_schedule,
            "risk_level": self.risk_level,
            "confidence": round(self.confidence, 3),
            "reasoning": self.reasoning,
            "source_keys": list(self.source_data.keys()),
            "timestamp": self.timestamp,
        }


class StrategyGenerator:
    """Generates strategies from intelligence inputs."""

    CONTENT_TYPES = ["educational", "entertaining", "inspiring", "promotional", "conversational"]
    RISK_THRESHOLDS = {"low": 0.8, "medium": 0.5, "high": 0.0}

    def __init__(self) -> None:
        self._generation_count = 0

    def generate(
        self,
        topic: str,
        score: float,
        intent: str = "educational",
        trend_data: Optional[Dict[str, Any]] = None,
        audience_data: Optional[Dict[str, Any]] = None,
        competitor_data: Optional[Dict[str, Any]] = None,
        content_data: Optional[Dict[str, Any]] = None,
        horizon: str = "short",
    ) -> GeneratedStrategy:
        """Generate a strategy from combined intelligence inputs."""
        strategy = GeneratedStrategy(name=f"{intent}_on_{topic}", horizon=horizon)
        strategy.source_data = {
            "topic": topic,
            "score": score,
            "intent": intent,
            "trend": trend_data or {},
            "audience": audience_data or {},
            "competitor": competitor_data or {},
            "content": content_data or {},
        }

        # Goals
        strategy.goals = self._build_goals(topic, intent, horizon)

        # Tactics
        strategy.tactics = self._build_tactics(intent, score, trend_data)

        # Content mix
        strategy.content_mix = self._build_content_mix(intent, trend_data)

        # Post schedule
        strategy.post_schedule = self._build_schedule(audience_data, trend_data)

        # Risk
        strategy.risk_level = self._assess_risk(score, competitor_data)

        # Confidence
        strategy.confidence = self._calculate_confidence(
            score, trend_data, audience_data, competitor_data, content_data
        )

        # Reasoning
        strategy.reasoning = self._build_reasoning(
            topic, intent, score, trend_data, audience_data, competitor_data
        )

        self._generation_count += 1
        return strategy

    def generate_batch(
        self, topics: List[Dict[str, Any]]
    ) -> List[GeneratedStrategy]:
        """Generate strategies for multiple topics."""
        results: List[GeneratedStrategy] = []
        for t in topics:
            results.append(self.generate(
                topic=t.get("topic", ""),
                score=t.get("score", 50.0),
                intent=t.get("intent", "educational"),
                trend_data=t.get("trend_data"),
                audience_data=t.get("audience_data"),
                competitor_data=t.get("competitor_data"),
                content_data=t.get("content_data"),
                horizon=t.get("horizon", "short"),
            ))
        return results

    def _build_goals(self, topic: str, intent: str, horizon: str) -> List[Dict[str, Any]]:
        goals: List[Dict[str, Any]] = []
        if horizon == "short":
            goals.append({"goal": f"Publish {intent} post on {topic}", "priority": "high", "timeframe": "today"})
        elif horizon == "medium":
            goals.append({"goal": f"Build content series around {topic}", "priority": "medium", "timeframe": "1_week"})
            goals.append({"goal": f"Engage audience on {topic}", "priority": "medium", "timeframe": "2_weeks"})
        else:
            goals.append({"goal": f"Establish authority in {topic}", "priority": "high", "timeframe": "1_month"})
            goals.append({"goal": f"Grow audience interested in {topic}", "priority": "medium", "timeframe": "3_months"})
        return goals

    def _build_tactics(self, intent: str, score: float, trend_data: Optional[Dict]) -> List[Dict[str, Any]]:
        tactics: List[Dict[str, Any]] = [{"action": "write_post", "priority": "HIGH", "effort": "medium"}]
        if score > 75:
            tactics.append({"action": "generate_image", "priority": "HIGH", "effort": "low"})
        if intent == "educational":
            tactics.append({"action": "create_carousel", "priority": "MEDIUM", "effort": "high"})
        if trend_data and trend_data.get("momentum", 0) > 0.7:
            tactics.append({"action": "publish_immediately", "priority": "CRITICAL", "effort": "low"})
        return tactics

    def _build_content_mix(self, intent: str, trend_data: Optional[Dict]) -> Dict[str, float]:
        mix: Dict[str, float] = {}
        if intent == "educational":
            mix = {"educational": 0.6, "inspiring": 0.2, "conversational": 0.2}
        elif intent == "promotional":
            mix = {"promotional": 0.4, "educational": 0.3, "entertaining": 0.3}
        elif intent == "entertaining":
            mix = {"entertaining": 0.5, "conversational": 0.3, "educational": 0.2}
        else:
            mix = {"educational": 0.33, "entertaining": 0.33, "conversational": 0.34}
        if trend_data and trend_data.get("virality_score", 0) > 0.8:
            mix["entertaining"] = mix.get("entertaining", 0) + 0.1
        return mix

    def _build_schedule(self, audience_data: Optional[Dict], trend_data: Optional[Dict]) -> List[Dict[str, Any]]:
        schedule: List[Dict[str, Any]] = []
        peak_hours = [9, 12, 18, 20]  # default
        if audience_data and "peak_hours" in audience_data:
            peak_hours = audience_data["peak_hours"]
        for hour in peak_hours[:3]:
            schedule.append({
                "time": f"{hour:02d}:00",
                "day": "today",
                "reason": "peak audience hours" if audience_data else "default peak time",
            })
        return schedule

    def _assess_risk(self, score: float, competitor_data: Optional[Dict]) -> str:
        competition = 0.5
        if competitor_data:
            competition = competitor_data.get("competition_level", 0.5)
        if score > 80 and competition < 0.6:
            return "low"
        if score < 50 or competition > 0.8:
            return "high"
        return "medium"

    def _calculate_confidence(
        self, score: float, trend_data: Optional[Dict],
        audience_data: Optional[Dict], competitor_data: Optional[Dict],
        content_data: Optional[Dict],
    ) -> float:
        components: List[float] = []
        components.append(min(score / 100.0, 1.0))
        if trend_data:
            components.append(trend_data.get("confidence", 0.7))
        if audience_data:
            components.append(audience_data.get("confidence", 0.7))
        if competitor_data:
            comp = competitor_data.get("competition_level", 0.5)
            components.append(max(0.0, 1.0 - comp))
        if content_data:
            components.append(content_data.get("quality_score", 0.7))
        if not components:
            return 0.5
        return round(sum(components) / len(components), 3)

    def _build_reasoning(
        self, topic: str, intent: str, score: float,
        trend_data: Optional[Dict], audience_data: Optional[Dict],
        competitor_data: Optional[Dict],
    ) -> List[str]:
        reasons: List[str] = []
        reasons.append(f"Topic '{topic}' scored {score:.0f}/100")
        reasons.append(f"Intent classified as '{intent}'")
        if trend_data:
            momentum = trend_data.get("momentum", 0)
            if momentum > 0.7:
                reasons.append("High trend momentum — prioritize immediacy")
            elif momentum < 0.3:
                reasons.append("Low trend momentum — consider waiting")
        if audience_data:
            engagement = audience_data.get("expected_engagement", 0)
            if engagement > 0.7:
                reasons.append("High audience engagement expected")
        if competitor_data:
            comp = competitor_data.get("competition_level", 0.5)
            if comp < 0.3:
                reasons.append("Low competition — good opportunity window")
            elif comp > 0.8:
                reasons.append("High competition — differentiate content")
        return reasons

    @property
    def generation_count(self) -> int:
        return self._generation_count
