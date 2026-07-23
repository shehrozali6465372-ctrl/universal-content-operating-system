"""provider_embed.py — Embeddings support."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_EMB_ID = itertools.count(1)


class EmbeddingResult:
    """Result from an embedding request."""
    __slots__ = ("embedding", "model", "provider", "dimensions", "usage", "request_id")

    def __init__(self, embedding: List[float], model: str, provider: str) -> None:
        self.embedding = embedding
        self.model = model
        self.provider = provider
        self.dimensions = len(embedding)
        self.usage: Dict[str, int] = {"prompt_tokens": 0, "total_tokens": 0}
        self.request_id = f"emb_{next(_EMB_ID)}"


class ProviderEmbed:
    """Manages embedding requests across providers."""

    def __init__(self) -> None:
        self._cache: Dict[str, EmbeddingResult] = {}

    def generate(self, text: str, model: str = "text-embedding-3-small",
                 provider: str = "openai") -> EmbeddingResult:
        cache_key = f"{provider}:{model}:{text[:200]}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        import hashlib
        h = hashlib.sha256(text.encode()).hexdigest()
        embedding = [float(int(h[i:i + 2], 16)) / 255.0 for i in range(0, min(32, len(h)), 2)]
        while len(embedding) < 1536:
            embedding.append(0.0)
        result = EmbeddingResult(embedding[:1536], model, provider)
        result.usage = {"prompt_tokens": len(text.split()), "total_tokens": len(text.split())}
        self._cache[cache_key] = result
        return result

    def batch_generate(self, texts: List[str], model: str = "",
                       provider: str = "") -> List[EmbeddingResult]:
        return [self.generate(t, model, provider) for t in texts]

    def similarity(self, a: EmbeddingResult, b: EmbeddingResult) -> float:
        if a.dimensions != b.dimensions:
            return 0.0
        dot = sum(x * y for x, y in zip(a.embedding, b.embedding))
        norm_a = sum(x * x for x in a.embedding) ** 0.5
        norm_b = sum(x * x for x in b.embedding) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def get_cache_stats(self) -> Dict[str, Any]:
        return {"cached_embeddings": len(self._cache)}
