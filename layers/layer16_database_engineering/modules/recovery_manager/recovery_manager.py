"""Recovery-plan execution with real callable steps and failure visibility."""
from __future__ import annotations
from dataclasses import dataclass,field
from enum import Enum
from threading import RLock
from time import time
from typing import Any,Dict,List
from uuid import uuid4

class RecoveryState(str,Enum):
    HEALTHY="healthy"; DEGRADED="degraded"; RECOVERING="recovering"; FAILED="failed"

@dataclass(slots=True)
class RecoveryPlan:
    name:str; steps:List[Dict[str,Any]]
    plan_id:str=field(default_factory=lambda:uuid4().hex[:12]); status:str="created"; created_at:float=field(default_factory=time); executed_at:float=0.0
    def to_dict(self)->Dict[str,Any]: return {"plan_id":self.plan_id,"name":self.name,"status":self.status,"steps":len(self.steps)}

class RecoveryManager:
    def __init__(self)->None: self._state=RecoveryState.HEALTHY; self._plans={}; self._history=[]; self._lock=RLock()
    def create_plan(self,name:str,steps:List[Dict[str,Any]])->RecoveryPlan:
        if not name or not steps: raise ValueError("name and at least one recovery step are required")
        if any(not callable(s.get("execute")) for s in steps): raise ValueError("each recovery step requires an execute callable")
        plan=RecoveryPlan(name,list(steps))
        with self._lock: self._plans[plan.plan_id]=plan
        return plan
    def execute_plan(self,plan_id:str)->Dict[str,Any]:
        with self._lock:
            plan=self._plans.get(plan_id)
            if plan is None: return {"error":"not_found"}
            if plan.status=="executing": return {"error":"already_running"}
            plan.status="executing"; self._state=RecoveryState.RECOVERING; plan.executed_at=time()
        completed=[]
        try:
            for i,step in enumerate(plan.steps):
                name=str(step.get("name",f"step_{i}")); step["execute"](); completed.append(name)
        except Exception as exc:
            with self._lock:
                plan.status="failed"; self._state=RecoveryState.FAILED
                result={"status":"failed","error":str(exc),"completed_steps":completed,"plan":plan.to_dict()}; self._history.append(result); return result
        with self._lock:
            plan.status="completed"; self._state=RecoveryState.HEALTHY
            result={"status":"completed","completed_steps":completed,"plan":plan.to_dict()}; self._history.append(result); return result
    def get_state(self)->str:
        with self._lock: return self._state.value
    def list_plans(self)->List[Dict[str,Any]]:
        with self._lock: return [p.to_dict() for p in self._plans.values()]
    def get_history(self)->List[Dict[str,Any]]:
        with self._lock: return list(self._history)
