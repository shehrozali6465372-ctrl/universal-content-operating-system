"""Thread-safe directed acyclic task dependency graph."""
from __future__ import annotations
import threading
from typing import Any, Dict, List, Set

class TaskGraph:
    def __init__(self)->None:
        self._adj:Dict[str,Set[str]]={}; self._reverse:Dict[str,Set[str]]={}; self._lock=threading.RLock()
    def add_task(self,task_id:str)->None:
        if not task_id: raise ValueError("task_id must be non-empty")
        with self._lock:
            self._adj.setdefault(task_id,set()); self._reverse.setdefault(task_id,set())
    def remove_task(self,task_id:str)->bool:
        with self._lock:
            if task_id not in self._adj and task_id not in self._reverse: return False
            for dep in self._reverse.get(task_id,set()): self._adj[dep].discard(task_id)
            for child in self._adj.get(task_id,set()): self._reverse[child].discard(task_id)
            self._adj.pop(task_id,None); self._reverse.pop(task_id,None); return True
    def add_edge(self,from_id:str,to_id:str)->None:
        if not from_id or not to_id: raise ValueError("task ids must be non-empty")
        if from_id==to_id: raise ValueError("self dependency is not allowed")
        with self._lock:
            self.add_task(from_id); self.add_task(to_id)
            if to_id in self._adj[from_id]: return
            self._adj[from_id].add(to_id); self._reverse[to_id].add(from_id)
            if self.has_cycle():
                self._adj[from_id].remove(to_id); self._reverse[to_id].remove(from_id)
                raise ValueError("dependency cycle detected")
    def get_dependencies(self,task_id:str)->List[str]:
        with self._lock: return sorted(self._reverse.get(task_id,set()))
    def get_dependents(self,task_id:str)->List[str]:
        with self._lock: return sorted(self._adj.get(task_id,set()))
    def get_ready_tasks(self,completed:Set[str])->List[str]:
        with self._lock:
            return sorted(t for t in self._adj if t not in completed and self._reverse[t].issubset(completed))
    def has_cycle(self)->bool:
        visiting:set[str]=set(); visited:set[str]=set()
        def dfs(node:str)->bool:
            visiting.add(node)
            for child in self._adj.get(node,set()):
                if child in visiting: return True
                if child not in visited and dfs(child): return True
            visiting.remove(node); visited.add(node); return False
        return any(dfs(node) for node in self._adj if node not in visited)
    def get_stats(self)->Dict[str,Any]:
        with self._lock: return {"nodes":len(self._adj),"edges":sum(len(v) for v in self._adj.values())}