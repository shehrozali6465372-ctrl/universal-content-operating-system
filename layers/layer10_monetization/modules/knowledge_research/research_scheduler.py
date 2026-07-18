"""ResearchScheduler — Schedule automatic research."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_RST_COUNTER = itertools.count(1)

SCHEDULE_TYPES = ("hourly", "daily", "weekly", "monthly", "event_based")


class ScheduledResearch:
    """A scheduled research job."""

    __slots__ = ("job_id", "name", "schedule_type", "query", "platforms",
                 "last_run", "next_run", "enabled")

    def __init__(self, name: str = "", schedule_type: str = "daily") -> None:
        self.job_id: str = f"srjob_{next(_RST_COUNTER)}"
        self.name = name
        self.schedule_type = schedule_type if schedule_type in SCHEDULE_TYPES else "daily"
        self.query: str = ""
        self.platforms: List[str] = []
        self.last_run: float = 0.0
        self.next_run: float = 0.0
        self.enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"job_id": self.job_id, "name": self.name,
                "schedule_type": self.schedule_type, "enabled": self.enabled}


class ResearchScheduler:
    """Schedule hourly, daily, weekly, monthly, and event-based research."""

    def __init__(self) -> None:
        self._jobs: List[ScheduledResearch] = []

    def schedule(self, name: str, schedule_type: str = "daily",
                 query: str = "", platforms: Optional[List[str]] = None) -> ScheduledResearch:
        job = ScheduledResearch(name, schedule_type)
        job.query = query
        job.platforms = platforms or ["universal"]
        self._jobs.append(job)
        return job

    def get_job(self, job_id: str) -> ScheduledResearch:
        for j in self._jobs:
            if j.job_id == job_id:
                return j
        return None

    def get_by_type(self, schedule_type: str) -> List[ScheduledResearch]:
        return [j for j in self._jobs if j.schedule_type == schedule_type]

    def get_enabled(self) -> List[ScheduledResearch]:
        return [j for j in self._jobs if j.enabled]

    def get_all(self) -> List[ScheduledResearch]:
        return list(self._jobs)

    def get_stats(self) -> Dict[str, Any]:
        types = {}
        for j in self._jobs:
            types[j.schedule_type] = types.get(j.schedule_type, 0) + 1
        return {"total": len(self._jobs), "by_type": types}

from typing import Optional
