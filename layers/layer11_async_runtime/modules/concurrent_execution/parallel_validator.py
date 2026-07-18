"""ParallelValidator — Validate parallel config."""
from __future__ import annotations
from typing import Any, Dict, List

class Parallelvalidator:
    def __init__(self) -> None:
        self._data: List[Dict[str, Any]] = []
    def record(self, data: Dict[str, Any]) -> None:
        self._data.append(data)
        if len(self._data) > 500: self._data = self._data[-500:]
    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._data)}
