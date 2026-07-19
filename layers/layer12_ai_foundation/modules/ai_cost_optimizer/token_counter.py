"""TokenCounter — count and estimate tokens."""
from __future__ import annotations
from typing import Dict

class TokenCounter:
    @staticmethod
    def count_words(text: str) -> int:
        return len(text.split())
    @staticmethod
    def estimate_tokens(text: str) -> int:
        words = len(text.split())
        chars = len(text)
        return max(int(words * 1.3 + chars * 0.04), 1)
    @staticmethod
    def count_batch(texts: list) -> Dict[str, int]:
        total_tokens = 0
        total_words = 0
        for t in texts:
            total_words += TokenCounter.count_words(t)
            total_tokens += TokenCounter.estimate_tokens(t)
        return {"total_words": total_words, "total_tokens": total_tokens, "count": len(texts)}
