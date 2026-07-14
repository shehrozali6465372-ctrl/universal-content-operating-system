"""Strategy Engine — short-term and long-term content strategy planning."""
from typing import Dict, List, Optional

class StrategyPlan:
    __slots__ = ("plan_id", "horizon", "goals", "tactics", "metrics", "confidence")
    def __init__(self, plan_id: str = "", horizon: str = "short"):
        self.plan_id = plan_id or f"plan_{hash(horizon) % 100000}"
        self.horizon = horizon
        self.goals: List[str] = []
        self.tactics: List[Dict] = []
        self.metrics: Dict[str, float] = {}
        self.confidence = 0.0
    def to_dict(self) -> dict:
        return {"plan_id": self.plan_id, "horizon": self.horizon, "goals": self.goals,
                "tactics": self.tactics, "metrics": self.metrics, "confidence": self.confidence}

class StrategyEngine:
    def __init__(self):
        self._plans: Dict[str, StrategyPlan] = {}
    def create_short_term(self, topic: str, score: float, intent: str) -> StrategyPlan:
        plan = StrategyPlan(horizon="short")
        plan.goals = [f"Create {intent} content about {topic}"]
        plan.tactics = [{"action": "write_post", "priority": "HIGH"}, {"action": "generate_image", "priority": "MEDIUM"}]
        plan.metrics = {"expected_engagement": score * 0.01, "urgency": 0.8}
        plan.confidence = min(0.95, score / 100)
        self._plans[plan.plan_id] = plan
        return plan
    def create_long_term(self, niche: str, trends: List[str]) -> StrategyPlan:
        plan = StrategyPlan(horizon="long")
        plan.goals = [f"Build authority in {niche}"] + [f"Cover trend: {t}" for t in trends[:5]]
        plan.tactics = [{"action": "content_series", "duration": "30 days"}, {"action": "community_building"}]
        plan.metrics = {"growth_target": 0.15, "consistency_target": 0.9}
        plan.confidence = 0.7
        self._plans[plan.plan_id] = plan
        return plan
    def get_plan(self, plan_id: str) -> Optional[StrategyPlan]:
        return self._plans.get(plan_id)
    def list_plans(self, horizon: Optional[str] = None) -> List[StrategyPlan]:
        plans = list(self._plans.values())
        if horizon: plans = [p for p in plans if p.horizon == horizon]
        return plans
