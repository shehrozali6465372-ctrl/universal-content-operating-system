"""
Semantic Clusterer — Sprint 4 (v4.0)

Groups similar topics/content into clusters using embedding similarity.

Public API:
    cluster(texts, threshold) -> List[Cluster]
    assign(text, clusters) -> int
    get_cluster(cluster_id) -> Cluster
    merge_clusters(cluster_a, cluster_b) -> Cluster
    summary() -> Dict

Version: 4.0.0
"""

from __future__ import annotations
from typing import Dict, List, Optional


class Cluster:
    """A group of semantically similar texts."""

    __slots__ = ("cluster_id", "label", "texts", "centroid_words", "size")

    def __init__(self, cluster_id: int = 0, label: str = ""):
        self.cluster_id = cluster_id
        self.label = label
        self.texts: List[str] = []
        self.centroid_words: List[str] = []
        self.size: int = 0

    def add(self, text: str) -> None:
        self.texts.append(text)
        self.size = len(self.texts)
        self._update_centroid()

    def _update_centroid(self) -> None:
        word_freq: Dict[str, int] = {}
        for text in self.texts:
            for word in text.lower().split():
                if len(word) >= 3:
                    word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: -x[1])
        self.centroid_words = [w for w, _ in sorted_words[:5]]
        if not self.label and self.centroid_words:
            self.label = " ".join(self.centroid_words[:2])

    def to_dict(self) -> Dict:
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "size": self.size,
            "texts": list(self.texts),
            "centroid_words": list(self.centroid_words),
        }


class SemanticClusterer:
    """Groups semantically similar texts into clusters.

    Usage::

        clusterer = SemanticClusterer()
        clusters = clusterer.cluster([
            "GPT-5 is a large language model",
            "ChatGPT uses AI technology",
            "Bitcoin price is rising",
            "Crypto market is growing",
        ], threshold=0.3)
        for c in clusters:
            print(c.label, c.size)
    """

    def __init__(self) -> None:
        self._clusters: List[Cluster] = []
        self._next_id = 0
        self._text_to_cluster: Dict[str, int] = {}

    def cluster(self, texts: List[str], threshold: float = 0.3,
                similarity_fn=None) -> List[Cluster]:
        """Cluster texts by semantic similarity.

        Args:
            texts: List of text strings.
            threshold: Minimum similarity to group into same cluster.
            similarity_fn: Function(text_a, text_b) -> float.
                          If None, uses word overlap similarity.

        Returns:
            List of Cluster objects.
        """
        if not texts:
            return []

        sim_fn = similarity_fn or self._default_similarity
        self._clusters.clear()
        self._text_to_cluster.clear()
        self._next_id = 0

        for text in texts:
            assigned = False
            for cluster in self._clusters:
                # Compare against centroid
                centroid_text = " ".join(cluster.centroid_words)
                sim = sim_fn(text, centroid_text)
                if sim >= threshold:
                    cluster.add(text)
                    self._text_to_cluster[text] = cluster.cluster_id
                    assigned = True
                    break

            if not assigned:
                c = Cluster(self._next_id)
                self._next_id += 1
                c.add(text)
                self._clusters.append(c)
                self._text_to_cluster[text] = c.cluster_id

        return list(self._clusters)

    def assign(self, text: str, similarity_fn=None) -> int:
        """Assign a new text to the most similar existing cluster.

        Returns cluster_id, or -1 if no cluster is similar enough.
        """
        sim_fn = similarity_fn or self._default_similarity
        best_cluster = -1
        best_sim = 0.0

        for cluster in self._clusters:
            centroid_text = " ".join(cluster.centroid_words)
            sim = sim_fn(text, centroid_text)
            if sim > best_sim:
                best_sim = sim
                best_cluster = cluster.cluster_id

        if best_sim >= 0.2:
            for c in self._clusters:
                if c.cluster_id == best_cluster:
                    c.add(text)
                    self._text_to_cluster[text] = best_cluster
                    break
            return best_cluster

        return -1

    def get_cluster(self, cluster_id: int) -> Optional[Cluster]:
        for c in self._clusters:
            if c.cluster_id == cluster_id:
                return c
        return None

    def get_clusters(self) -> List[Cluster]:
        return list(self._clusters)

    def merge_clusters(self, id_a: int, id_b: int) -> Optional[Cluster]:
        """Merge two clusters into one."""
        ca = self.get_cluster(id_a)
        cb = self.get_cluster(id_b)
        if not ca or not cb:
            return None

        merged = Cluster(id_a, f"{ca.label} + {cb.label}")
        for text in ca.texts + cb.texts:
            merged.add(text)

        self._clusters = [c for c in self._clusters if c.cluster_id not in (id_a, id_b)]
        self._clusters.append(merged)
        return merged

    def summary(self) -> Dict:
        return {
            "total_clusters": len(self._clusters),
            "total_texts": sum(c.size for c in self._clusters),
            "clusters": [{"id": c.cluster_id, "label": c.label, "size": c.size}
                         for c in self._clusters],
        }

    def reset(self) -> None:
        self._clusters.clear()
        self._text_to_cluster.clear()
        self._next_id = 0

    @staticmethod
    def _default_similarity(text_a: str, text_b: str) -> float:
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / max(len(union), 1)
