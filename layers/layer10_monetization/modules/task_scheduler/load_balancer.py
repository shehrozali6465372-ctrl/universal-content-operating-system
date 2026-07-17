"""Load Balancer — Distribute tasks across workers."""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional
from layers.layer10_monetization.modules.task_scheduler.worker_pool import WorkerPool, Worker


class LoadBalancer:
    """Distribute workload across workers using various algorithms."""

    LEAST_LOADED = "least_loaded"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    RANDOM = "random"
    AFFINITY = "affinity"

    def __init__(self, algorithm: str = "least_loaded") -> None:
        self._algorithm = algorithm
        self._round_robin_index: int = 0
        self._affinity_map: Dict[str, str] = {}
        self._weights: Dict[str, float] = {}

    @property
    def algorithm(self) -> str:
        return self._algorithm

    def select_worker(self, pool: WorkerPool, task_layer: str = "") -> Optional[Worker]:
        idle = pool.get_idle_workers()
        if not idle:
            return None

        if self._algorithm == self.LEAST_LOADED:
            return self._select_least_loaded(idle)
        elif self._algorithm == self.ROUND_ROBIN:
            return self._select_round_robin(idle)
        elif self._algorithm == self.WEIGHTED:
            return self._select_weighted(idle)
        elif self._algorithm == self.RANDOM:
            return random.choice(idle)
        elif self._algorithm == self.AFFINITY:
            return self._select_affinity(idle, task_layer)
        return idle[0]

    def _select_least_loaded(self, workers: List[Worker]) -> Worker:
        return min(workers, key=lambda w: w.tasks_completed + w.tasks_failed)

    def _select_round_robin(self, workers: List[Worker]) -> Worker:
        idx = self._round_robin_index % len(workers)
        self._round_robin_index += 1
        return workers[idx]

    def _select_weighted(self, workers: List[Worker]) -> Worker:
        def score(w: Worker) -> float:
            weight = self._weights.get(w.worker_id, 1.0)
            load = w.cpu_usage + w.memory_usage
            return load / max(0.1, weight)
        return min(workers, key=score)

    def _select_affinity(self, workers: List[Worker], layer: str) -> Worker:
        preferred_id = self._affinity_map.get(layer)
        if preferred_id:
            for w in workers:
                if w.worker_id == preferred_id:
                    return w
        return self._select_least_loaded(workers)

    def set_affinity(self, layer: str, worker_id: str) -> None:
        self._affinity_map[layer] = worker_id

    def set_weight(self, worker_id: str, weight: float) -> None:
        self._weights[worker_id] = weight

    def detect_hotspots(self, pool: WorkerPool) -> List[Dict[str, Any]]:
        hotspots = []
        for worker in pool.get_busy_workers():
            if worker.cpu_usage > 0.8 or worker.memory_usage > 0.8:
                hotspots.append({
                    "worker_id": worker.worker_id,
                    "cpu": worker.cpu_usage,
                    "memory": worker.memory_usage,
                    "severity": "high" if worker.cpu_usage > 0.9 else "medium",
                })
        return hotspots

    def rebalance(self, pool: WorkerPool) -> int:
        busy = pool.get_busy_workers()
        hotspots = self.detect_hotspots(pool)
        return len(hotspots)
