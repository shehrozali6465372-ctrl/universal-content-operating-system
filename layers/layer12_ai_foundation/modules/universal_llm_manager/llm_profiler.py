"""LLMProfiler for universal_llm_manager."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LLMProfiler:
    def __init__(self) -> None:
        self._data: List[Dict[str, Any]] = []
    def record(self, data: Dict[str, Any]) -> None:
        self._data.append({"data": data, "time": time.time()})
        if len(self._data) > 500:
            self._data = self._data[-500:]
    def get_recent(self, count: int = 20) -> List[Dict[str, Any]]:
        return self._data[-count:]
    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._data)}
