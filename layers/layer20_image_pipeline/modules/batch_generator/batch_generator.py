"""Production-safe batch image generation orchestration."""
from __future__ import annotations
from enum import Enum
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

class BatchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class BatchJob:
    __slots__ = ("batch_id","prompts","status","results","errors","created_at","finished_at","metadata")
    def __init__(self, prompts: List[Dict[str, Any]]) -> None:
        self.batch_id = uuid.uuid4().hex
        self.prompts = [dict(p) for p in prompts]
        self.status = BatchStatus.PENDING
        self.results: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.created_at = time.time()
        self.finished_at = 0.0
        self.metadata: Dict[str, Any] = {}
    def to_dict(self) -> Dict[str, Any]:
        return {"batch_id":self.batch_id,"status":self.status.value,"total":len(self.prompts),
                "completed":len(self.results),"errors":len(self.errors),
                "created_at":self.created_at,"finished_at":self.finished_at}

class BatchGenerator:
    def __init__(self) -> None:
        self._batches: Dict[str, BatchJob] = {}
        self._generator_fn: Optional[Callable[[Dict[str, Any]], Any]] = None
        self._lock = threading.RLock()
    def set_generator(self, fn: Callable[[Dict[str, Any]], Any]) -> None:
        if not callable(fn):
            raise TypeError("generator must be callable")
        with self._lock:
            self._generator_fn = fn
    def create_batch(self, prompts: List[Dict[str, Any]]) -> BatchJob:
        if not isinstance(prompts, list):
            raise TypeError("prompts must be a list")
        if any(not isinstance(p, dict) for p in prompts):
            raise TypeError("every prompt must be a dictionary")
        job = BatchJob(prompts)
        with self._lock:
            self._batches[job.batch_id] = job
        return job
    def execute_batch(self, batch_id: str) -> Dict[str, Any]:
        with self._lock:
            job = self._batches.get(batch_id)
            if job is None:
                return {"error":"batch_not_found"}
            if job.status in (BatchStatus.COMPLETED, BatchStatus.FAILED):
                return job.to_dict()
            if job.status == BatchStatus.RUNNING:
                return {"error":"batch_already_running","batch_id":batch_id}
            if self._generator_fn is None:
                job.status = BatchStatus.FAILED
                job.errors.append({"index":None,"error":"generator_not_configured"})
                job.finished_at = time.time()
                return job.to_dict()
            generator = self._generator_fn
            job.status = BatchStatus.RUNNING
        for index, prompt in enumerate(job.prompts):
            try:
                result = generator(prompt)
                if not isinstance(result, dict):
                    raise TypeError("generator result must be a dictionary")
                with self._lock:
                    job.results.append(dict(result))
            except Exception as exc:
                with self._lock:
                    job.errors.append({"index":index,"error_type":type(exc).__name__,"error":str(exc)})
        with self._lock:
            job.status = BatchStatus.COMPLETED if not job.errors else BatchStatus.FAILED
            job.finished_at = time.time()
            return job.to_dict()
    def get_batch(self, batch_id: str) -> Optional[BatchJob]:
        with self._lock:
            return self._batches.get(batch_id)
    def list_batches(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [b.to_dict() for b in self._batches.values()]
