"""bloom_filter.py — Redis Bloom filter."""
from __future__ import annotations
import hashlib
from typing import List


class BloomFilter:
    """Probabilistic Bloom filter."""

    def __init__(self, size: int = 1000, hash_count: int = 3) -> None:
        self._bits = [False] * size
        self._size = size
        self._hash_count = hash_count
        self._count: int = 0

    def _hashes(self, item: str) -> List[int]:
        results = []
        for i in range(self._hash_count):
            h = hashlib.md5(f"{item}_{i}".encode()).hexdigest()
            results.append(int(h, 16) % self._size)
        return results

    def add(self, item: str) -> None:
        for pos in self._hashes(item):
            self._bits[pos] = True
        self._count += 1

    def might_contain(self, item: str) -> bool:
        return all(self._bits[pos] for pos in self._hashes(item))

    def count(self) -> int:
        return self._count

    def fill_rate(self) -> float:
        return sum(self._bits) / self._size

    def clear(self) -> None:
        self._bits = [False] * self._size
        self._count = 0
