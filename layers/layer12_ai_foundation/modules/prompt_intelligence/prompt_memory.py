"""PromptMemory — remember successful and failed prompt strategies."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class PromptMemory:
    """Memory for prompt strategies — successes and failures."""

    def __init__(self, max_entries: int = 1000) -> None:
        self.max_entries = max_entries
        self._successful: List[Dict[str, Any]] = []
        self._failed: List[Dict[str, Any]] = []

    def store_success(self, prompt: str, output: str, score: float,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        self._successful.append({
            "prompt_hash": hash(prompt) % 10**8,
            "output_preview": output[:100],
            "score": score,
            "metadata": metadata or {},
            "timestamp": time.time(),
        })
        if len(self._successful) > self.max_entries:
            self._successful = self._successful[-self.max_entries:]

    def store_failure(self, prompt: str, output: str, reason: str,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        self._failed.append({
            "prompt_hash": hash(prompt) % 10**8,
            "output_preview": output[:100],
            "reason": reason,
            "metadata": metadata or {},
            "timestamp": time.time(),
        })
        if len(self._failed) > self.max_entries:
            self._failed = self._failed[-self.max_entries:]

    def recall_successful(self, limit: int = 5) -> List[Dict[str, Any]]:
        return sorted(self._successful, key=lambda e: e["score"], reverse=True)[:limit]

    def recall_failures(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self._failed[-limit:]

    @property
    def success_rate(self) -> float:
        total = len(self._successful) + len(self._failed)
        return len(self._successful) / total if total > 0 else 0.0

    def count(self) -> int:
        return len(self._successful) + len(self._failed)

    def clear(self) -> None:
        self._successful.clear()
        self._failed.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {"successes": len(self._successful), "failures": len(self._failed),
                "success_rate": round(self.success_rate, 4)}
