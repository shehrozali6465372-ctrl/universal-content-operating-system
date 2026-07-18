"""hyperloglog.py — Redis HyperLogLog."""
from __future__ import annotations
import hashlib


class HyperLogLog:
    """Approximate cardinality counting."""

    def __init__(self, precision: int = 14) -> None:
        self._registers = [0] * (1 << precision)
        self._precision = precision
        self._count: int = 0

    def add(self, item: str) -> bool:
        h = int(hashlib.md5(item.encode()).hexdigest(), 16)
        index = h & ((1 << self._precision) - 1)
        if index == 0:
            index = 1
        leading_zeros = 0
        remaining = h >> self._precision
        while remaining and not (remaining & 1):
            leading_zeros += 1
            remaining >>= 1
        changed = leading_zeros > self._registers[index]
        if changed:
            self._registers[index] = leading_zeros
        self._count += 1
        return changed

    def count(self) -> int:
        alpha = 0.7213 / (1 + 1.079 / len(self._registers))
        raw = alpha * len(self._registers) ** 2 / sum(2 ** -r for r in self._registers if r > 0)
        return int(raw)

    def merge(self, other: "HyperLogLog") -> None:
        for i in range(len(self._registers)):
            self._registers[i] = max(self._registers[i], other._registers[i])
