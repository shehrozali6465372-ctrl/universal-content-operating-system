"""Bounded health checks with timeout handling."""
from __future__ import annotations
import threading,time
from enum import Enum
from typing import Any,Callable,Dict,List,Optional
class HealthLevel(str,Enum): HEALTHY="healthy";DEGRADED="degraded";UNHEALTHY="unhealthy"
class HealthCheck:
    __slots__=("name","check_fn","interval","last_check","consecutive_failures","max_failures","timeout","metadata")
    def __init__(self,name:str,check_fn:Callable[[],Any],interval:float=60.0,max_failures:int=3,timeout:float=5.0)->None:
        if not name.strip() or interval<0 or max_failures<=0 or timeout<=0:raise ValueError("invalid health check configuration")
        self.name,self.check_fn,self.interval=name,check_fn,interval;self.last_check=0.0;self.consecutive_failures=0;self.max_failures=max_failures;self.timeout=timeout;self.metadata={}
class HealthMonitor:
    def __init__(self,history_size:int=1000)->None:
        if history_size<=0:raise ValueError("history_size must be positive")
        self._lock=threading.RLock();self._history_size=history_size;self._checks={};self._results={};self._history=[]
    def register(self,name:str,check_fn:Callable[[],Any],interval:float=60.0,max_failures:int=3,timeout:float=5.0)->HealthCheck:
        c=HealthCheck(name,check_fn,interval,max_failures,timeout)
        with self._lock:self._checks[name]=c
        return c
    def unregister(self,name:str)->bool:
        with self._lock:self._results.pop(name,None);return self._checks.pop(name,None) is not None
    def check(self,name:str)->Dict[str,Any]:
        with self._lock:c=self._checks.get(name)
        if c is None:return {"name":name,"status":"unhealthy","error":"not_found"}
        result_holder: Dict[str, Any] = {}
        error_holder: List[BaseException] = []
        done = threading.Event()

        def run_check() -> None:
            try:
                result_holder["value"] = c.check_fn()
            except BaseException as exc:
                error_holder.append(exc)
            finally:
                done.set()

        worker = threading.Thread(target=run_check, name="health-check-" + name, daemon=True)
        worker.start()
        timed_out = not done.wait(c.timeout)
        if timed_out:
            result = {"error": "health check timed out after %.2fs" % c.timeout}
        elif error_holder:
            result = {"error": str(error_holder[0])}
        else:
            result = result_holder.get("value")
        with self._lock:
            if timed_out or isinstance(result,dict) and "error" in result:c.consecutive_failures+=1
            else:c.consecutive_failures=0
            failures=c.consecutive_failures
        if timed_out or isinstance(result,dict) and "error" in result:status=HealthLevel.UNHEALTHY if failures>=c.max_failures else HealthLevel.DEGRADED
        else:status=HealthLevel.HEALTHY if (result.get("healthy",True) if isinstance(result,dict) else bool(result)) else HealthLevel.DEGRADED
        now=time.time();entry={"name":name,"status":status.value,"details":result,"failures":failures,"time":now}
        with self._lock:
            c.last_check=now;self._results[name]=entry;self._history.append(dict(entry))
            if len(self._history)>self._history_size:del self._history[:-self._history_size]
        return entry
    def check_all(self)->Dict[str,Any]:
        with self._lock:names=list(self._checks)
        results={n:self.check(n) for n in names};statuses=[r["status"] for r in results.values()]
        overall="unhealthy" if "unhealthy" in statuses else "degraded" if "degraded" in statuses else "healthy"
        return {"overall":overall,"checks":results}
    def get_unhealthy(self)->List[str]:
        with self._lock:return [n for n,r in self._results.items() if r["status"]=="unhealthy"]
    def list_checks(self)->List[str]:
        with self._lock:return list(self._checks)
    def get_history(self,name:Optional[str]=None)->List[Dict[str,Any]]:
        with self._lock:v=self._history if name is None else [h for h in self._history if h["name"]==name];return [dict(x) for x in v]
    def count(self)->int:
        with self._lock:return len(self._checks)
