"""
Deduplicator
Layer 2: Research Engine — Module 5

Detects and removes duplicate knowledge entries:
- Exact hash matching
- Fuzzy similarity detection (Jaccard)
- Near-duplicate detection
- Duplicate statistics
"""

from typing import Dict, List, Optional, Set, Tuple
from layers.layer02_research.modules.knowledge_collector.knowledge_entry import KnowledgeEntry


class Deduplicator:
    """Deduplication engine for knowledge entries."""

    def __init__(self, similarity_threshold: float = 0.7):
        self._similarity_threshold = similarity_threshold
        self._hash_index: Dict[str, List[str]] = {}
        self._duplicate_count = 0

    @property
    def similarity_threshold(self) -> float:
        return self._similarity_threshold

    @similarity_threshold.setter
    def similarity_threshold(self, value: float):
        self._similarity_threshold = max(0.0, min(1.0, value))

    def check_exact(self, entry: KnowledgeEntry) -> Optional[str]:
        """Check if an entry with the same hash already exists."""
        if entry.content_hash in self._hash_index:
            return self._hash_index[entry.content_hash][0]
        return None

    def register(self, entry: KnowledgeEntry) -> str:
        """Register an entry for future dedup checks. Returns original entry_id if duplicate."""
        if entry.content_hash not in self._hash_index:
            self._hash_index[entry.content_hash] = [entry.entry_id]
        else:
            self._hash_index[entry.content_hash].append(entry.entry_id)
        return entry.entry_id

    def find_duplicates(self, entries: List[KnowledgeEntry]) -> Dict[str, List[str]]:
        """Find all duplicate groups in a set of entries."""
        hash_groups: Dict[str, List[str]] = {}
        for entry in entries:
            if entry.content_hash not in hash_groups:
                hash_groups[entry.content_hash] = []
            hash_groups[entry.content_hash].append(entry.entry_id)

        return {h: ids for h, ids in hash_groups.items() if len(ids) > 1}

    def mark_duplicates(self, entries: List[KnowledgeEntry]) -> int:
        """Mark duplicate entries. Returns count of duplicates found."""
        hash_groups: Dict[str, List[str]] = {}
        for entry in entries:
            if entry.content_hash not in hash_groups:
                hash_groups[entry.content_hash] = []
            hash_groups[entry.content_hash].append(entry)

        count = 0
        for h, group in hash_groups.items():
            if len(group) > 1:
                # Keep the first, mark rest as duplicates
                original = group[0]
                for dup in group[1:]:
                    dup.is_duplicate = True
                    dup.duplicate_of = original.entry_id
                    count += 1

        self._duplicate_count += count
        return count

    def similarity_score(self, text_a: str, text_b: str) -> float:
        """Jaccard similarity between two texts."""
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0

    def find_similar(
        self, entry: KnowledgeEntry, all_entries: List[KnowledgeEntry], top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """Find entries similar to the given entry."""
        scores = []
        for other in all_entries:
            if other.entry_id == entry.entry_id:
                continue
            sim = self.similarity_score(entry.content, other.content)
            if sim >= self._similarity_threshold:
                scores.append((other.entry_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]

    def fuzzy_dedup(
        self, entries: List[KnowledgeEntry], threshold: Optional[float] = None
    ) -> int:
        """Mark near-duplicates using fuzzy similarity."""
        thresh = threshold if threshold is not None else self._similarity_threshold
        count = 0
        seen: Set[str] = set()

        for i, entry_a in enumerate(entries):
            if entry_a.entry_id in seen or entry_a.is_duplicate:
                continue
            for j in range(i + 1, len(entries)):
                entry_b = entries[j]
                if entry_b.entry_id in seen or entry_b.is_duplicate:
                    continue
                sim = self.similarity_score(entry_a.content, entry_b.content)
                if sim >= thresh:
                    entry_b.is_duplicate = True
                    entry_b.duplicate_of = entry_a.entry_id
                    seen.add(entry_b.entry_id)
                    count += 1

        self._duplicate_count += count
        return count

    def get_stats(self) -> dict:
        return {
            "total_hashes_indexed": len(self._hash_index),
            "total_duplicates_found": self._duplicate_count,
        }

    def clear(self):
        self._hash_index.clear()
        self._duplicate_count = 0
