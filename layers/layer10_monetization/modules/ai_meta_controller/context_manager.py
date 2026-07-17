"""Context Manager — Understand current situation."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class ContextManager:
    """Manage current operational context."""

    def __init__(self) -> None:
        self._context: Dict[str, Any] = {
            "campaign": "", "trend": "", "platform": "",
            "audience": "", "topic": "", "language": "en",
            "region": "global", "time": time.time(),
        }
        self._history: List[Dict[str, Any]] = []

    def set(self, key: str, value: Any) -> None:
        self._context[key] = value
        self._context["time"] = time.time()

    def get(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        return dict(self._context)

    def update(self, data: Dict[str, Any]) -> None:
        self._context.update(data)
        self._context["time"] = time.time()

    def snapshot(self) -> Dict[str, Any]:
        snap = dict(self._context)
        self._history.append(snap)
        return snap

    def restore(self, index: int = -1) -> bool:
        if self._history:
            idx = index if index >= 0 else len(self._history) + index
            if 0 <= idx < len(self._history):
                self._context = dict(self._history[idx])
                return True
        return False

    def clear(self) -> None:
        self._context = {k: "" for k in self._context if k != "time"}
        self._context["language"] = "en"
        self._context["region"] = "global"
        self._context["time"] = time.time()

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._history[-limit:]
