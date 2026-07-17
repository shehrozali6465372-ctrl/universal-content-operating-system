"""Scheduler Policy — Different scheduling algorithms."""
from __future__ import annotations
from typing import Dict, List, Optional
from layers.layer10_monetization.modules.task_scheduler.task import Task


class SchedulerPolicy:
    """Select next task based on scheduling policy."""

    FIFO = "fifo"
    PRIORITY = "priority"
    ROUND_ROBIN = "round_robin"
    SHORTEST_JOB_FIRST = "shortest_job_first"
    EARLIEST_DEADLINE = "earliest_deadline"
    WEIGHTED_FAIR = "weighted_fair"

    def __init__(self, policy: str = "priority") -> None:
        self._policy = policy if policy in (
            self.FIFO, self.PRIORITY, self.ROUND_ROBIN,
            self.SHORTEST_JOB_FIRST, self.EARLIEST_DEADLINE, self.WEIGHTED_FAIR,
        ) else self.PRIORITY
        self._round_robin_index: int = 0
        self._fair_weights: Dict[str, float] = {}

    @property
    def name(self) -> str:
        return self._policy

    def select_next(self, tasks: List[Task]) -> Optional[Task]:
        if not tasks:
            return None
        candidates = [t for t in tasks if t.status in ("pending", "queued")]
        if not candidates:
            return None

        if self._policy == self.FIFO:
            return self._select_fifo(candidates)
        elif self._policy == self.PRIORITY:
            return self._select_priority(candidates)
        elif self._policy == self.ROUND_ROBIN:
            return self._select_round_robin(candidates)
        elif self._policy == self.SHORTEST_JOB_FIRST:
            return self._select_sjf(candidates)
        elif self._policy == self.EARLIEST_DEADLINE:
            return self._select_edf(candidates)
        elif self._policy == self.WEIGHTED_FAIR:
            return self._select_weighted(candidates)
        return candidates[0]

    def _select_fifo(self, tasks: List[Task]) -> Task:
        return min(tasks, key=lambda t: t.created_at)

    def _select_priority(self, tasks: List[Task]) -> Task:
        return min(tasks, key=lambda t: (t.priority, t.created_at))

    def _select_round_robin(self, tasks: List[Task]) -> Task:
        if not tasks:
            return None
        idx = self._round_robin_index % len(tasks)
        self._round_robin_index += 1
        return tasks[idx]

    def _select_sjf(self, tasks: List[Task]) -> Task:
        return min(tasks, key=lambda t: t.estimated_duration)

    def _select_edf(self, tasks: List[Task]) -> Task:
        with_deadline = [t for t in tasks if t.deadline is not None]
        if with_deadline:
            return min(with_deadline, key=lambda t: t.deadline)
        return tasks[0]

    def _select_weighted(self, tasks: List[Task]) -> Task:
        def score(t: Task) -> float:
            weight = self._fair_weights.get(t.layer, 1.0)
            return t.priority / max(0.1, weight)
        return min(tasks, key=score)

    def set_weight(self, layer: str, weight: float) -> None:
        self._fair_weights[layer] = weight

    def rebalance(self, tasks: List[Task]) -> List[Task]:
        if self._policy == self.PRIORITY:
            return sorted(tasks, key=lambda t: (t.priority, t.created_at))
        elif self._policy == self.SHORTEST_JOB_FIRST:
            return sorted(tasks, key=lambda t: t.estimated_duration)
        return tasks
