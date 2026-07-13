"""
Decision Logger Module
Layer 1: Core System — Module 6

Tracks every AI decision with reasoning, confidence, and data source.
This is the key differentiator — Agent remembers WHY it made each decision.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class DecisionLogger:
    """Logs AI decisions with full reasoning chain."""

    def __init__(self, log_path: str = "logs/decisions.log"):
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._decisions: List[Dict] = []

    def log_decision(
        self,
        question: str,
        answer: str,
        confidence: float,
        data_sources: List[str],
        reasoning: str,
        module: str = "agent",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Log a single AI decision."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module": module,
            "question": question,
            "answer": answer,
            "confidence": min(max(confidence, 0.0), 1.0),
            "reasoning": reasoning,
            "data_sources": data_sources,
            "tags": tags or [],
        }
        self._decisions.append(entry)
        with open(self._path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
        return entry

    def get_decisions(
        self,
        module: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 50,
    ) -> List[Dict]:
        """Get logged decisions with filters."""
        results = self._decisions
        if module:
            results = [d for d in results if d["module"] == module]
        if min_confidence > 0:
            results = [d for d in results if d["confidence"] >= min_confidence]
        return results[-limit:]

    def get_from_file(self, limit: int = 50) -> List[Dict]:
        """Read decisions from file."""
        if not self._path.exists():
            return []
        entries = []
        with open(self._path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries[-limit:]

    def get_average_confidence(self, module: Optional[str] = None) -> float:
        """Calculate average confidence score."""
        decisions = self.get_decisions(module=module, limit=10000)
        if not decisions:
            return 0.0
        return sum(d["confidence"] for d in decisions) / len(decisions)

    def get_decision_stats(self) -> Dict[str, Any]:
        """Get statistics about decisions."""
        all_d = self._decisions
        if not all_d:
            return {"total": 0}
        confidences = [d["confidence"] for d in all_d]
        return {
            "total": len(all_d),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "by_module": self._count_by("module"),
            "by_source": self._count_by_list("data_sources"),
        }

    def _count_by(self, field: str) -> Dict[str, int]:
        counts = {}
        for d in self._decisions:
            val = d.get(field, "unknown")
            counts[val] = counts.get(val, 0) + 1
        return counts

    def _count_by_list(self, field: str) -> Dict[str, int]:
        counts = {}
        for d in self._decisions:
            for item in d.get(field, []):
                counts[item] = counts.get(item, 0) + 1
        return counts

    def clear(self) -> None:
        self._decisions.clear()
        if self._path.exists():
            self._path.write_text("")
