"""MultiModelMemory — remember past multi-model operations and outcomes."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class MultiModelMemory:
    """Memory for multi-model intelligence operations."""

    def __init__(self, max_entries: int = 1000) -> None:
        self.max_entries = max_entries
        self._entries: List[Dict[str, Any]] = []

    def store(self, prompt: str, best_model: str, consensus_score: float,
              confidence: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        entry = {
            "prompt_hash": hash(prompt) % 10**8,
            "best_model": best_model,
            "consensus_score": consensus_score,
            "confidence": confidence,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]

    def recall(self, prompt: str) -> Optional[Dict[str, Any]]:
        prompt_hash = hash(prompt) % 10**8
        for entry in reversed(self._entries):
            if entry["prompt_hash"] == prompt_hash:
                return entry
        return None

    def get_best_model_for_type(self, task_type: str) -> Optional[str]:
        type_entries = [e for e in self._entries if e.get("metadata", {}).get("task_type") == task_type]
        if not type_entries:
            return None
        model_scores: Dict[str, List[float]] = {}
        for e in type_entries:
            model_scores.setdefault(e["best_model"], []).append(e["confidence"])
        return max(model_scores, key=lambda m: sum(model_scores[m]) / len(model_scores[m]))

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {"count": len(self._entries), "max_entries": self.max_entries}
