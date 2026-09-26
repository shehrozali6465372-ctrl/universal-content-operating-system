"""Compatibility error tracker with bounded state."""
from __future__ import annotations
import threading,time,uuid
from enum import Enum
from typing import Any,Dict,List,Optional
class ErrorSeverity(str,Enum): LOW="low";MEDIUM="medium";HIGH="high";CRITICAL="critical"
class ErrorEntry:
    __slots__=("error_id","error_type","message","severity","source","stack_trace","count","first_seen","last_seen","metadata")
    def __init__(self,error_type:str,message:str,severity:ErrorSeverity=ErrorSeverity.MEDIUM,source:str="")->None:
        self.error_id=str(uuid.uuid4());self.error_type=error_type;self.message=message;self.severity=severity;self.source=source;self.stack_trace="";self.count=1;self.first_seen=self.last_seen=time.time();self.metadata={}
    def to_dict(self)->Dict[str,Any]:
        return {"error_id":self.error_id,"type":self.error_type,"message":self.message[:200],"severity":self.severity.value,"source":self.source,"count":self.count,"first_seen":self.first_seen,"last_seen":self.last_seen}
class ErrorTracker:
    def __init__(self,history_size:int=1000)->None:
        if history_size<=0:raise ValueError("history_size must be positive")
        self._lock=threading.RLock();self._history_size=history_size;self._errors={};self._history=[]
    def track(self,error_type:str,message:str,severity:ErrorSeverity=ErrorSeverity.MEDIUM,source:str="")->ErrorEntry:
        if not error_type.strip() or not message.strip():raise ValueError("error_type and message are required")
        key=f"{error_type}:{message[:100]}"
        with self._lock:
            e=self._errors.get(key)
            if e:e.count+=1;e.last_seen=time.time();return e
            e=ErrorEntry(error_type,message,severity,source);self._errors[key]=e;self._history.append(e.to_dict())
            if len(self._history)>self._history_size:del self._history[:-self._history_size]
            return e
    def get_error(self,error_id:str)->Optional[ErrorEntry]:
        with self._lock:return next((e for e in self._errors.values() if e.error_id==error_id),None)
    def list_errors(self,severity:Optional[ErrorSeverity]=None)->List[Dict[str,Any]]:
        with self._lock:
            v=list(self._errors.values());v=[e for e in v if severity is None or e.severity==severity];return [e.to_dict() for e in v]
    def get_top_errors(self,limit:int=10)->List[Dict[str,Any]]:
        if limit<=0:raise ValueError("limit must be positive")
        with self._lock:return [e.to_dict() for e in sorted(self._errors.values(),key=lambda e:(-e.count,e.error_id))[:limit]]
    def clear(self)->int:
        with self._lock:n=len(self._errors);self._errors.clear();return n
    def stats(self)->Dict[str,Any]:
        with self._lock:
            return {"unique_errors":len(self._errors),"total_occurrences":sum(e.count for e in self._errors.values()),"by_severity":{s.value:sum(e.severity==s for e in self._errors.values()) for s in ErrorSeverity}}
