"""BatchGenerator — generate images in batches."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class BatchStatus(str, Enum):
    PENDING = "pending"; RUNNING = "running"; COMPLETED = "completed"; FAILED = "failed"


class BatchJob:
    __slots__ = ("batch_id", "prompts", "status", "results", "errors",
                 "created_at", "finished_at", "metadata")

    def __init__(self, prompts: List[Dict[str, Any]]) -> None:
        self.batch_id = str(uuid.uuid4())[:12]
        self.prompts = prompts
        self.status = BatchStatus.PENDING
        self.results: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.created_at = time.time()
        self.finished_at: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"batch_id": self.batch_id, "status": self.status.value,
                "total": len(self.prompts), "completed": len(self.results),
                "errors": len(self.errors)}


class BatchGenerator:
    def __init__(self) -> None:
        self._batches: Dict[str, BatchJob] = {}
        self._generator_fn: Optional[Callable] = None

    def set_generator(self, fn: Callable) -> None:
        self._generator_fn = fn

    def create_batch(self, prompts: List[Dict[str, Any]]) -> BatchJob:
        job = BatchJob(prompts)
        self._batches[job.batch_id] = job
        return job

    def execute_batch(self, batch_id: str) -> Dict[str, Any]:
        job = self._batches.get(batch_id)
        if not job:
            return {"error": "batch_not_found"}
        job.status = BatchStatus.RUNNING
        for i, prompt in enumerate(job.prompts):
            try:
                if self._generator_fn:
                    result = self._generator_fn(prompt)
                else:
                    result = {"url": f"generated_{i}.png", "prompt": prompt}
                job.results.append(result)
            except Exception as exc:
                job.errors.append({"index": i, "error": str(exc)})
        job.status = BatchStatus.COMPLETED if not job.errors else BatchStatus.FAILED
        job.finished_at = time.time()
        return job.to_dict()

    def get_batch(self, batch_id: str) -> Optional[BatchJob]:
        return self._batches.get(batch_id)

    def list_batches(self) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self._batches.values()]
