"""RuntimeManager — lifecycle and health orchestration for Layer 11."""
from __future__ import annotations
import threading
from typing import Any, Dict, Optional
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_config import RuntimeConfig
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_state import RuntimeState
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_metrics import RuntimeMetrics
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_events import RuntimeEvents
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_health import RuntimeHealth
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_memory import RuntimeMemory
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_profiler import RuntimeProfiler
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_registry import RuntimeRegistry
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_report import RuntimeReportGenerator
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_validator import RuntimeValidator
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_monitor import RuntimeMonitor

class RuntimeManager:
    """Main runtime lifecycle manager."""
    def __init__(self, config: Optional[RuntimeConfig] = None) -> None:
        self.config=config or RuntimeConfig()
        self.state=RuntimeState(); self.metrics=RuntimeMetrics(); self.events=RuntimeEvents()
        self.health=RuntimeHealth(); self.memory=RuntimeMemory(); self.profiler=RuntimeProfiler()
        self.registry=RuntimeRegistry(); self.report_generator=RuntimeReportGenerator()
        self.validator=RuntimeValidator(); self.monitor=RuntimeMonitor(); self._lock=threading.RLock()
        self.health.register_check("config", self._config_health)
        self.health.register_check("state", self._state_health)
    def _config_health(self)->bool:
        self.config.validate(); return True
    def _state_health(self)->bool:
        return self.state.current not in {RuntimeState.ERROR, RuntimeState.STOPPING}
    def start(self)->bool:
        with self._lock:
            if not self.state.transition(RuntimeState.STARTING): return False
            self.events.publish("runtime_starting","manager")
            self.metrics.increment("start_count")
            if not self.state.transition(RuntimeState.RUNNING):
                self.state.transition(RuntimeState.ERROR); return False
            self.events.publish("runtime_started","manager")
            self.memory.save_checkpoint(RuntimeState.RUNNING)
            return True
    def stop(self)->bool:
        with self._lock:
            if not self.state.transition(RuntimeState.STOPPING): return False
            self.events.publish("runtime_stopping","manager")
            if not self.state.transition(RuntimeState.STOPPED):
                self.state.transition(RuntimeState.ERROR); return False
            self.events.publish("runtime_stopped","manager")
            self.memory.save_checkpoint(RuntimeState.STOPPED)
            return True
    def pause(self)->bool:
        with self._lock:
            if not self.state.transition(RuntimeState.PAUSED): return False
            self.events.publish("runtime_paused","manager"); return True
    def resume(self)->bool:
        with self._lock:
            if not self.state.transition(RuntimeState.RUNNING): return False
            self.events.publish("runtime_resumed","manager"); return True
    def restart(self)->bool:
        with self._lock:
            current=self.state.current
            if current not in {RuntimeState.RUNNING,RuntimeState.PAUSED,RuntimeState.STOPPED,RuntimeState.ERROR}:
                return False
            if current in {RuntimeState.RUNNING,RuntimeState.PAUSED,RuntimeState.ERROR}:
                if current==RuntimeState.ERROR: self.state.transition(RuntimeState.STOPPED)
                elif not self.state.transition(RuntimeState.STOPPING): return False
                else: self.state.transition(RuntimeState.STOPPED)
            return self.start()
    def status(self)->Dict[str,Any]:
        with self._lock:
            return {"state":self.state.to_dict(),"metrics":self.metrics.to_dict(),
                    "health":self.health.get_stats(),"registry":self.registry.get_stats()}
    def health_check(self)->Dict[str,Any]:
        results=self.health.run_checks()
        return {"healthy":self.health.is_healthy(),"checks":[r.to_dict() for r in results]}
    def generate_report(self, report_type:str="status")->Dict[str,Any]:
        report=self.report_generator.generate(report_type,self.status()); return report.to_dict()
    def get_full_status(self)->Dict[str,Any]:
        with self._lock:
            return {"state":self.state.current,"metrics":self.metrics.to_dict(),
                    "health":self.health.is_healthy(),"registry_count":len(self.registry.get_all()),
                    "memory_checkpoints":len(self.memory.get_all()),"events":self.events.get_stats()}
