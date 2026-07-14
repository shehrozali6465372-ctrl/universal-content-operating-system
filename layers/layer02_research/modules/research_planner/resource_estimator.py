"""
Resource Estimator
Layer 2: Research Engine — Module 9

Estimates resources for research plans:
- Time estimation
- API call estimation
- Memory usage estimation
- Cost estimation (USD)
- Quality expectation
"""

from typing import Dict, List
from layers.layer02_research.modules.research_planner.research_plan import PlanTask, ResearchPlan


# API cost per call (approximate)
API_COST_PER_CALL = {
    "trend_discovery": 0.001,
    "topic_intelligence": 0.002,
    "competitor_analysis": 0.003,
    "audience_research": 0.002,
    "knowledge_collector": 0.001,
    "fact_verification": 0.004,
    "research_memory": 0.0005,
    "topic_scoring": 0.001,
}

# Memory footprint per module (MB estimate)
MODULE_MEMORY_MB = {
    "trend_discovery": 15.0,
    "topic_intelligence": 20.0,
    "competitor_analysis": 30.0,
    "audience_research": 25.0,
    "knowledge_collector": 40.0,
    "fact_verification": 20.0,
    "research_memory": 35.0,
    "topic_scoring": 10.0,
}


class ResourceEstimate:
    """Resource estimate for a plan or task."""

    __slots__ = (
        "estimated_time_min", "estimated_api_calls",
        "estimated_memory_mb", "estimated_cost_usd",
        "estimated_disk_mb", "expected_confidence",
        "expected_quality",
    )

    def __init__(self):
        self.estimated_time_min = 0.0
        self.estimated_api_calls = 0
        self.estimated_memory_mb = 0.0
        self.estimated_cost_usd = 0.0
        self.estimated_disk_mb = 0.0
        self.expected_confidence = 0.0
        self.expected_quality = 0.0

    def to_dict(self) -> dict:
        return {
            "estimated_time_min": round(self.estimated_time_min, 2),
            "estimated_api_calls": self.estimated_api_calls,
            "estimated_memory_mb": round(self.estimated_memory_mb, 2),
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "estimated_disk_mb": round(self.estimated_disk_mb, 2),
            "expected_confidence": round(self.expected_confidence, 3),
            "expected_quality": round(self.expected_quality, 3),
        }


class ResourceEstimator:
    """Estimates resources required for research plans."""

    # Module execution time multiplier for complexity
    MODULE_TIME_MULTIPLIER = {
        "trend_discovery": 1.0,
        "topic_intelligence": 1.2,
        "competitor_analysis": 1.5,
        "audience_research": 1.3,
        "knowledge_collector": 1.8,
        "fact_verification": 1.6,
        "research_memory": 0.8,
        "topic_scoring": 0.7,
    }

    def estimate_task(self, task: PlanTask) -> ResourceEstimate:
        """Estimate resources for a single task."""
        est = ResourceEstimate()
        module = task.module

        est.estimated_time_min = task.estimated_time_min * self.MODULE_TIME_MULTIPLIER.get(module, 1.0)
        est.estimated_api_calls = task.estimated_api_calls
        est.estimated_memory_mb = max(task.estimated_memory_mb, MODULE_MEMORY_MB.get(module, 10.0))
        cost_per = API_COST_PER_CALL.get(module, 0.002)
        est.estimated_cost_usd = task.estimated_api_calls * cost_per
        est.estimated_disk_mb = est.estimated_memory_mb * 0.3

        # Expected confidence based on module type
        verification_modules = {"fact_verification", "research_memory"}
        base_confidence = 0.95 if module in verification_modules else 0.80
        est.expected_confidence = base_confidence
        est.expected_quality = min(1.0, base_confidence * 0.95)

        return est

    def estimate_plan(self, plan: ResearchPlan) -> ResourceEstimate:
        """Estimate total resources for a complete research plan."""
        est = ResourceEstimate()

        for task in plan.tasks:
            task_est = self.estimate_task(task)
            est.estimated_time_min += task_est.estimated_time_min
            est.estimated_api_calls += task_est.estimated_api_calls
            est.estimated_memory_mb = max(est.estimated_memory_mb, task_est.estimated_memory_mb)
            est.estimated_cost_usd += task_est.estimated_cost_usd
            est.estimated_disk_mb += task_est.estimated_disk_mb

        # Overall expected confidence is weighted by critical tasks
        critical_tasks = [t for t in plan.tasks if t.priority in ("CRITICAL", "HIGH")]
        if critical_tasks:
            confidences = [self.estimate_task(t).expected_confidence for t in critical_tasks]
            est.expected_confidence = sum(confidences) / len(confidences)
        est.expected_quality = est.expected_confidence * 0.9

        return est

    def estimate_cost_breakdown(self, plan: ResearchPlan) -> Dict[str, float]:
        """Get cost breakdown by module."""
        breakdown: Dict[str, float] = {}
        for task in plan.tasks:
            est = self.estimate_task(task)
            module = task.module or "unknown"
            breakdown[module] = breakdown.get(module, 0.0) + est.estimated_cost_usd
        return {k: round(v, 6) for k, v in breakdown.items()}

    def estimate_time_breakdown(self, plan: ResearchPlan) -> Dict[str, float]:
        """Get time breakdown by module."""
        breakdown: Dict[str, float] = {}
        for task in plan.tasks:
            est = self.estimate_task(task)
            module = task.module or "unknown"
            breakdown[module] = breakdown.get(module, 0.0) + est.estimated_time_min
        return {k: round(v, 2) for k, v in breakdown.items()}

    def compare_plans(self, plans: List[ResearchPlan]) -> List[Dict]:
        """Compare resource estimates across multiple plans."""
        results = []
        for plan in plans:
            est = self.estimate_plan(plan)
            results.append({
                "plan_id": plan.plan_id,
                "topic": plan.topic,
                "tasks": len(plan.tasks),
                "estimate": est.to_dict(),
            })
        return sorted(results, key=lambda r: r["estimate"]["estimated_cost_usd"])

    def is_feasible(self, plan: ResearchPlan, max_time_min: float = 60.0,
                    max_cost_usd: float = 0.1, max_memory_mb: float = 256.0) -> bool:
        """Check if a plan is within resource constraints."""
        est = self.estimate_plan(plan)
        return (est.estimated_time_min <= max_time_min and
                est.estimated_cost_usd <= max_cost_usd and
                est.estimated_memory_mb <= max_memory_mb)
