"""Memory Merger — Merge similar or duplicate memory entries."""
from __future__ import annotations
from typing import Any, Dict, List


class MergedResult:
    """Result of merging multiple memory entries."""

    __slots__ = ("merged_id", "source_count", "resulting_entry",
                 "confidence", "information_loss")

    def __init__(self) -> None:
        self.merged_id: str = ""
        self.source_count: int = 0
        self.resulting_entry: Dict[str, Any] = {}
        self.confidence: float = 0.0
        self.information_loss: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "merged_id": self.merged_id,
            "source_count": self.source_count,
            "confidence": round(self.confidence, 3),
            "information_loss": self.information_loss,
        }


class MemoryMerger:
    """Merge similar memory entries to reduce redundancy."""

    def __init__(self) -> None:
        self._results: List[MergedResult] = []
        self._merge_count: int = 0

    def merge_by_keyword(self, entries: List[Dict[str, Any]],
                         keyword_field: str = "tags",
                         min_similarity: int = 2) -> List[MergedResult]:
        merged: Dict[str, List[Dict[str, Any]]] = {}
        for entry in entries:
            keywords = entry.get(keyword_field, [])
            if isinstance(keywords, list):
                for kw in keywords:
                    merged.setdefault(str(kw), []).append(entry)

        results = []
        for keyword, group in merged.items():
            if len(group) >= min_similarity:
                mr = MergedResult()
                mr.merged_id = f"mg_{keyword}_{self._merge_count}"
                mr.source_count = len(group)
                mr.resulting_entry = self._merge_entries(group)
                mr.confidence = round(
                    sum(e.get("confidence", 0.5) for e in group) / len(group), 3,
                )
                results.append(mr)
                self._results.append(mr)
                self._merge_count += 1
        return results

    def merge_by_type(self, entries: List[Dict[str, Any]],
                      type_field: str = "learning_type") -> List[MergedResult]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for entry in entries:
            etype = entry.get(type_field, "insight")
            grouped.setdefault(etype, []).append(entry)

        results = []
        for etype, group in grouped.items():
            if len(group) >= 2:
                mr = MergedResult()
                mr.merged_id = f"mt_{etype}_{self._merge_count}"
                mr.source_count = len(group)
                mr.resulting_entry = self._merge_entries(group)
                mr.confidence = round(
                    sum(e.get("confidence", 0.5) for e in group) / len(group), 3,
                )
                results.append(mr)
                self._results.append(mr)
                self._merge_count += 1
        return results

    def _merge_entries(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        if not entries:
            return merged
        merged["description"] = "; ".join(
            e.get("description", "") for e in entries if e.get("description")
        )
        merged["tags"] = list(set(
            t for e in entries for t in e.get("tags", []) if isinstance(t, str)
        ))
        merged["source_count"] = len(entries)
        merged["merged"] = True
        return merged

    def get_results(self) -> List[MergedResult]:
        return list(self._results)

    @property
    def merge_count(self) -> int:
        return self._merge_count
