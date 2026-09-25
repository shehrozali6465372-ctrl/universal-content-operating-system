"""TaskExecutor — deterministic sync/async callable execution."""
from __future__ import annotations
import asyncio
import inspect
import time
from typing import Any, Callable, Dict, Optional
from layers.layer11_async_runtime.modules.async_task_manager.task import Task

class TaskExecutor:
    def __init__(self)->None:
        self._completed=0; self._failed=0
    def execute(self,task:Task,func:Optional[Callable[...,Any]]=None)->Dict[str,Any]:
        start=time.monotonic()
        task.start()
        try:
            result=func() if func else None
            if inspect.isawaitable(result):
                result=asyncio.run(result)
            task.complete(result); self._completed+=1; success=True
        except Exception as exc:
            task.fail(str(exc)); self._failed+=1; success=False
        return {"task_id":task.id,"duration_ms":round((time.monotonic()-start)*1000,2),"success":success}
    def get_stats(self)->Dict[str,int]: return {"completed":self._completed,"failed":self._failed}