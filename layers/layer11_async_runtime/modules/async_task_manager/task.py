"""Task — Individual async task."""
from __future__ import annotations
from layers.layer11_async_runtime.modules.async_task_manager.models import AsyncTask, TaskState
import time

class Task:
    def __init__(self,name:str="",priority:int=1):
        self._task=AsyncTask(name,priority)
    @property
    def id(self): return self._task.task_id
    @property
    def state(self): return self._task.state
    def start(self): self._task.state=TaskState.RUNNING; self._task.started_at=time.time()
    def complete(self,result=None): self._task.state=TaskState.COMPLETED; self._task.result=result; self._task.completed_at=time.time()
    def fail(self,error:str=""): self._task.state=TaskState.FAILED; self._task.error=error; self._task.completed_at=time.time()
    def cancel(self): self._task.state=TaskState.CANCELLED
    def to_dict(self): return self._task.to_dict()
