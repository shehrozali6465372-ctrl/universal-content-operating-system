"""TaskGroup — Group related tasks."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class TaskGroup:
    def __init__(self,name:str=""):
        self.group_id=f"tg_{int(time.time()*1000)}"
        self.name=name
        self.task_ids:List[str]=[]
        self.status="active"
    def add_task(self,task_id:str): self.task_ids.append(task_id)
    def remove_task(self,task_id:str): self.task_ids=[t for t in self.task_ids if t!=task_id]
    def get_stats(self)->Dict[str,Any]: return {"group_id":self.group_id,"tasks":len(self.task_ids)}
