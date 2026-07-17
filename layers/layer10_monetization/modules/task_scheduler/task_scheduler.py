"""Task Scheduler — Main scheduler engine."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List, Optional
from layers.layer10_monetization.modules.task_scheduler.task import Task
from layers.layer10_monetization.modules.task_scheduler.priority_queue import PriorityQueue
from layers.layer10_monetization.modules.task_scheduler.scheduler_policy import SchedulerPolicy
from layers.layer10_monetization.modules.task_scheduler.resource_allocator import ResourceAllocator
from layers.layer10_monetization.modules.task_scheduler.worker_pool import WorkerPool
from layers.layer10_monetization.modules.task_scheduler.load_balancer import LoadBalancer
from layers.layer10_monetization.modules.task_scheduler.scheduler_events import (
    SchedulerEventBus, SchedulerEvent,
    EVENT_TASK_SCHEDULED, EVENT_TASK_STARTED, EVENT_TASK_COMPLETED,
    EVENT_TASK_FAILED, EVENT_TASK_RETRIED, EVENT_WORKER_ASSIGNED,
    EVENT_WORKER_RELEASED,
)
from layers.layer10_monetization.modules.task_scheduler.scheduler_metrics import SchedulerMetrics
from layers.layer10_monetization.modules.task_scheduler.scheduler_report import SchedulerReport

_TS_COUNTER = itertools.count(1)


class TaskScheduler:
    """Intelligent task scheduling engine with priority, load balancing, and resource allocation.

    Flow: Schedule → Queue → Select Policy → Allocate Resources → Assign Worker → Execute
    """

    def __init__(self, worker_count: int = 5, queue_size: int = 10000,
                 policy: str = "priority") -> None:
        self.queue = PriorityQueue(max_size=queue_size)
        self.policy = SchedulerPolicy(policy)
        self.worker_pool = WorkerPool(size=worker_count)
        self.load_balancer = LoadBalancer()
        self.resource_allocator = ResourceAllocator()
        self.event_bus = SchedulerEventBus()
        self.metrics = SchedulerMetrics()
        self._completed_tasks: List[Task] = []
        self._running_tasks: Dict[str, Task] = {}
        self._paused_tasks: Dict[str, Task] = {}

    def schedule_task(self, task: Task) -> bool:
        if not task.validate():
            return False
        if self.queue.is_full:
            self.event_bus.publish(SchedulerEvent(
                event_type="queue_full",
                task_id=task.task_id,
            ))
            return False
        success = self.queue.push(task)
        if success:
            self.metrics.record_task_scheduled()
            self.metrics.record_queue_size(self.queue.size)
            self.event_bus.publish(SchedulerEvent(
                event_type=EVENT_TASK_SCHEDULED,
                task_id=task.task_id,
            ))
        return success

    def execute_next(self, executor: Callable) -> Optional[Task]:
        task = self.policy.select_next(self.queue.get_all())
        if not task:
            return None

        self.queue.remove(task.task_id)
        worker = self.worker_pool.assign(task.task_id)
        if not worker:
            self.queue.push(task)
            return None

        self.event_bus.publish(SchedulerEvent(
            event_type=EVENT_WORKER_ASSIGNED,
            task_id=task.task_id,
            worker_id=worker.worker_id,
        ))

        if self.resource_allocator.allocate(task.task_id, task.resource_cost):
            task.start(worker.worker_id)
            self._running_tasks[task.task_id] = task
            self.metrics.record_task_completed(
                wait_time_ms=(time.time() - task.created_at) * 1000,
            )

            self.event_bus.publish(SchedulerEvent(
                event_type=EVENT_TASK_STARTED,
                task_id=task.task_id,
                worker_id=worker.worker_id,
            ))

            start = time.time()
            try:
                result = executor(task.layer)
                task.complete(result)
                self.metrics.record_task_completed(
                    execution_time_ms=(time.time() - start) * 1000,
                )
                self.event_bus.publish(SchedulerEvent(
                    event_type=EVENT_TASK_COMPLETED,
                    task_id=task.task_id,
                ))
            except Exception as e:
                task.fail(str(e))
                self.metrics.record_task_failed()
                self.event_bus.publish(SchedulerEvent(
                    event_type=EVENT_TASK_FAILED,
                    task_id=task.task_id,
                ))
            finally:
                self.resource_allocator.release(task.task_id)
                self.worker_pool.release(worker.worker_id, task.status == "completed")
                self._running_tasks.pop(task.task_id, None)
                self._completed_tasks.append(task)

                self.event_bus.publish(SchedulerEvent(
                    event_type=EVENT_WORKER_RELEASED,
                    task_id=task.task_id,
                    worker_id=worker.worker_id,
                ))

            return task
        else:
            self.worker_pool.release(worker.worker_id)
            self.queue.push(task)
            return None

    def pause_task(self, task_id: str) -> bool:
        task = self._running_tasks.pop(task_id, None)
        if task:
            task.pause()
            self._paused_tasks[task_id] = task
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        task = self._paused_tasks.pop(task_id, None)
        if task:
            task.resume()
            self._running_tasks[task_id] = task
            self.queue.push(task)
            return True
        return False

    def cancel_task(self, task_id: str) -> bool:
        task = self.queue.remove(task_id)
        if task:
            task.cancel()
            self._completed_tasks.append(task)
            return True
        task = self._running_tasks.pop(task_id, None)
        if task:
            task.cancel()
            self._completed_tasks.append(task)
            return True
        return False

    def reschedule_task(self, task_id: str, new_priority: int) -> bool:
        return self.queue.update_priority(task_id, new_priority)

    def retry_task(self, task_id: str) -> bool:
        for task in self._completed_tasks:
            if task.task_id == task_id and task.can_retry():
                task.retry()
                self._completed_tasks.remove(task)
                self.queue.push(task)
                self.metrics.record_retry()
                self.event_bus.publish(SchedulerEvent(
                    event_type=EVENT_TASK_RETRIED,
                    task_id=task.task_id,
                ))
                return True
        return False

    def get_queue_size(self) -> int:
        return self.queue.size

    def get_running_count(self) -> int:
        return len(self._running_tasks)

    def get_completed_count(self) -> int:
        return len(self._completed_tasks)

    def generate_report(self) -> SchedulerReport:
        report = SchedulerReport()
        queue_stats = self.queue.get_stats()
        worker_stats = self.worker_pool.get_stats()
        resource_stats = self.resource_allocator.get_stats()
        metrics = self.metrics.get_summary()

        report.set_queue_report(
            total=queue_stats["total"],
            by_priority={str(k): v for k, v in queue_stats["by_priority"].items()},
            avg_wait_ms=metrics["avg_wait_time_ms"],
        )
        report.set_worker_report(
            pool_size=worker_stats["pool_size"],
            idle=worker_stats["idle"],
            busy=worker_stats["busy"],
            completed=worker_stats["total_completed"],
        )
        report.set_resource_report(resource_stats["utilization"])
        report.set_performance_report(
            throughput=metrics["throughput_per_sec"],
            efficiency=metrics["scheduling_efficiency"],
            avg_exec_ms=metrics["avg_execution_time_ms"],
        )

        if worker_stats["idle"] == 0:
            report.add_recommendation("All workers busy — consider scaling up")
        if metrics["avg_wait_time_ms"] > 1000:
            report.add_recommendation("High wait times — consider adding workers")
        if metrics["scheduling_efficiency"] < 0.5:
            report.add_recommendation("Low efficiency — review scheduling policy")

        return report

    def get_health(self) -> Dict[str, Any]:
        return {
            "queue_size": self.queue.size,
            "running": self.get_running_count(),
            "completed": self.get_completed_count(),
            "workers": self.worker_pool.get_stats(),
            "metrics": self.metrics.get_summary(),
        }
