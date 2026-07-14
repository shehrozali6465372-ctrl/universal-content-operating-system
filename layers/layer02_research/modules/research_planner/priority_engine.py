"""
Priority Engine
Layer 2: Research Engine — Module 9

Assigns priorities to research tasks:
- Score-based priority assignment
- Urgency detection
- Impact estimation
- Critical path weighting
- Failure-based priority adjustment
"""

from typing import Dict, List, Optional
from layers.layer02_research.modules.research_planner.research_plan import PlanTask


class PriorityEngine:
    """Assign and adjust task priorities based on various signals."""

    PRIORITY_WEIGHTS = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
        "BACKGROUND": 0,
    }

    # Module importance mapping
    MODULE_IMPORTANCE = {
        "fact_verification": 10.0,
        "topic_scoring": 9.0,
        "knowledge_collector": 8.0,
        "trend_discovery": 7.0,
        "competitor_analysis": 7.0,
        "audience_research": 6.0,
        "topic_intelligence": 6.0,
        "research_memory": 5.0,
    }

    def assign_priorities(
        self,
        tasks: List[PlanTask],
        topic_scores: Optional[Dict[str, float]] = None,
    ) -> List[PlanTask]:
        """Assign priorities based on topic scores and module importance."""
        scores = topic_scores or {}
        for task in tasks:
            score = self._compute_priority_score(task, scores)
            task.priority = self._score_to_priority(score)
        return tasks

    def _compute_priority_score(self, task: PlanTask, scores: Dict[str, float]) -> float:
        """Compute a priority score (0-10) for a task."""
        base = 5.0

        # Module importance boost
        module_importance = self.MODULE_IMPORTANCE.get(task.module, 5.0)
        base += (module_importance - 5.0) * 0.3

        # Map topic scores to module relevance
        module_score_map = {
            "trend_discovery": "trend",
            "topic_intelligence": "topic",
            "competitor_analysis": "competition",
            "audience_research": "audience",
            "knowledge_collector": "knowledge",
            "fact_verification": "verification",
            "research_memory": "knowledge",
            "topic_scoring": "overall",
        }
        module_key = module_score_map.get(task.module, "")
        if module_key and module_key in scores:
            base += (scores[module_key] - 5.0) * 0.2

        # Tasks with many dependents are more critical
        base += min(1.0, len(task.dependencies) * 0.15)

        # API-heavy tasks get higher priority
        if task.estimated_api_calls > 3:
            base += 0.5

        # Long tasks get slight boost (do them early)
        if task.estimated_time_min > 5.0:
            base += 0.3

        return max(0.0, min(10.0, base))

    def _score_to_priority(self, score: float) -> str:
        """Convert a numeric score (0-10) to a priority string."""
        if score >= 8.0:
            return "CRITICAL"
        elif score >= 6.0:
            return "HIGH"
        elif score >= 4.0:
            return "MEDIUM"
        elif score >= 2.0:
            return "LOW"
        return "BACKGROUND"

    def get_execution_order(self, tasks: List[PlanTask]) -> List[PlanTask]:
        """Sort tasks by priority (highest first), then by estimated time (shortest first)."""
        return sorted(tasks, key=lambda t: (
            -self.PRIORITY_WEIGHTS.get(t.priority, 0),
            t.estimated_time_min,
        ))

    def adjust_for_failure(self, tasks: List[PlanTask], failed_task_id: str) -> List[PlanTask]:
        """Boost priority of tasks that depend on a failed task."""
        for task in tasks:
            if failed_task_id in task.dependencies:
                current_weight = self.PRIORITY_WEIGHTS.get(task.priority, 2)
                boosted_score = current_weight + 3.5
                task.priority = self._score_to_priority(min(10.0, boosted_score))
        return tasks

    def get_priority_distribution(self, tasks: List[PlanTask]) -> Dict[str, int]:
        """Get count of tasks per priority level."""
        dist: Dict[str, int] = {}
        for task in tasks:
            dist[task.priority] = dist.get(task.priority, 0) + 1
        return dist

    def rebalance(self, tasks: List[PlanTask]) -> List[PlanTask]:
        """Rebalance priorities to ensure no single level dominates excessively."""
        if len(tasks) <= 2:
            return tasks

        dist = self.get_priority_distribution(tasks)
        max_count = max(dist.values()) if dist else 0

        # If more than 60% of tasks are in one priority, downgrade some
        threshold = len(tasks) * 0.6
        if max_count > threshold:
            dominant = max(dist, key=dist.get)
            current_weight = self.PRIORITY_WEIGHTS.get(dominant, 2)
            if current_weight > 0:
                for task in tasks:
                    if task.priority == dominant:
                        task.priority = self._score_to_priority(float(current_weight))
                        break  # downgrade one at a time

        return tasks
