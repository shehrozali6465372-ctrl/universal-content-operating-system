"""Thread-safe, bounded runtime event bus."""
from __future__ import annotations
import itertools
import threading
import time
from typing import Any, Callable, Dict, List, Optional

_RE_COUNTER = itertools.count(1)

class RuntimeEvent:
    __slots__ = ("event_id","event_type","source","data","timestamp")
    def __init__(self,event_type:str="",source:str="")->None:
        self.event_id=f"re_{time.time_ns()}_{next(_RE_COUNTER)}"
        self.event_type=event_type
        self.source=source
        self.data:Dict[str,Any]={}
        self.timestamp=time.time()

class RuntimeEvents:
    def __init__(self,max_events:int=10000)->None:
        if max_events<1: raise ValueError("max_events must be >= 1")
        self._max_events=max_events
        self._subscribers:Dict[str,List[Callable[[RuntimeEvent],None]]]={}
        self._events:List[RuntimeEvent]=[]
        self._lock=threading.RLock()
    def publish(self,event_type:str,source:str="",data:Optional[Dict[str,Any]]=None)->RuntimeEvent:
        event=RuntimeEvent(event_type,source)
        if data: event.data=dict(data)
        with self._lock:
            self._events.append(event)
            if len(self._events)>self._max_events:
                del self._events[:len(self._events)-self._max_events]
            handlers=list(self._subscribers.get(event_type,()))
        for handler in handlers:
            try: handler(event)
            except Exception: continue
        return event
    def subscribe(self,event_type:str,handler:Callable[[RuntimeEvent],None])->None:
        if not callable(handler): raise TypeError("handler must be callable")
        with self._lock: self._subscribers.setdefault(event_type,[]).append(handler)
    def unsubscribe(self,event_type:str,handler:Callable[[RuntimeEvent],None])->bool:
        with self._lock:
            handlers=self._subscribers.get(event_type,[])
            if handler in handlers:
                handlers.remove(handler)
                return True
            return False
    def get_events(self,event_type:str="",count:int=50)->List[RuntimeEvent]:
        if count<0: raise ValueError("count must be >= 0")
        with self._lock:
            events=list(self._events)
        if event_type: events=[e for e in events if e.event_type==event_type]
        return events[-count:] if count else []
    def clear(self)->int:
        with self._lock:
            count=len(self._events); self._events.clear(); return count
    def get_stats(self)->Dict[str,Any]:
        with self._lock:
            types:Dict[str,int]={}
            for event in self._events: types[event.event_type]=types.get(event.event_type,0)+1
            return {"total_events":len(self._events),"by_type":types}