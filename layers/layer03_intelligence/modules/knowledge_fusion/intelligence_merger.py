"""Intelligence Merger - Merges intelligence objects from different modules."""
from __future__ import annotations
from typing import Any, Dict, List


class MergedIntelligence:
    __slots__ = ("topic", "merged_data", "source_count", "conflicts", "confidence")
    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.merged_data: Dict[str, Any] = {}
        self.source_count = 0
        self.conflicts: List[str] = []
        self.confidence = 0.0
    def to_dict(self) -> Dict:
        return {"topic": self.topic, "source_count": self.source_count,
                "conflicts": list(self.conflicts), "confidence": round(self.confidence, 3),
                "data_keys": list(self.merged_data.keys())}


class IntelligenceMerger:
    def merge(self, topic: str, intelligences: List[Dict]) -> MergedIntelligence:
        result = MergedIntelligence(topic)
        result.source_count = len(intelligences)
        key_values: Dict[str, List] = {}
        for intel in intelligences:
            for key, value in intel.items():
                key_values.setdefault(key, []).append(value)
        for key, values in key_values.items():
            if len(values) == 1:
                result.merged_data[key] = values[0]
            else:
                if all(isinstance(v, (int, float)) for v in values):
                    result.merged_data[key] = sum(values) / len(values)
                else:
                    result.merged_data[key] = values[-1]
        if len(intelligences) > 1:
            scores = [i.get("score", i.get("confidence", 0.5)) for i in intelligences]
            if isinstance(scores[0], (int, float)):
                result.confidence = 1.0 - (max(scores) - min(scores))
        return result
