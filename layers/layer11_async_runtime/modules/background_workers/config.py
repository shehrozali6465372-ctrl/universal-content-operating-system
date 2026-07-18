"""WorkerConfig — config for background_workers."""
from __future__ import annotations
from typing import Any, Dict, List

class WorkerConfig:
    def __init__(self) -> None:
        self._data: List[Dict[str, Any]] = []
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._data.append(data)
        return {"status": "ok", "processed": True}
    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._data)}
