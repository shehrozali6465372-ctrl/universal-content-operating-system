"""Task lifecycle wrapper with explicit state transitions."""
from __future__ import annotations
import time
from typing import Any, Optional
from layers.layer11_async_runtime.modules.async_task_manager.models import AsyncTask, TaskState

class Task:
    def __init__(self,name:str="",priority:int=1)->None:
        self._task=AsyncTask(name,priority)
    @property
    def id(self)->str: return self._task.task_id
    @property
    def state(self)->str: return self._task.state
    def start(self)->None:
        if self.state != TaskState.PENDING: raise RuntimeError("task is not pending")
        self._task.state=TaskState.RUNNING; self._task.started_at=time.time()
    def complete(self,result:Any=None)->None:
        if self.state != TaskState.RUNNING: raise RuntimeError("task is not running")
        self._task.state=TaskState.COMPLETED; self._task.result=result; self._task.completed_at=time.time()
    def fail(self,error:str="")->None:
        if self.state != TaskState.RUNNING: raise RuntimeError("task is not running")
        self._task.state=TaskState.FAILED; self._task.error=error; self._task.completed_at=time.time()
    def cancel(self)->None:
        if self.state not in (TaskState.PENDING,TaskState.RUNNING): raise RuntimeError("task cannot be cancelled")
        self._task.state=TaskState.CANCELLED; self._task.completed_at=time.time()
    def to_dict(self): return self._task.to_dict()