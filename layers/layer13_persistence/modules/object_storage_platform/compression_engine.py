"""compression_engine.py — Data compression support."""
from __future__ import annotations


class CompressionEngine:
    """Compresses and decompresses data."""

    def __init__(self) -> None:
        self._algorithms = ["gzip", "lz4", "zstd", "snappy"]
        self._default: str = "gzip"

    def compress(self, data: bytes, algorithm: str = "") -> bytes:
        algo = algorithm or self._default
        if algo == "gzip":
            import gzip
            return gzip.compress(data)
        return data

    def decompress(self, data: bytes, algorithm: str = "") -> bytes:
        algo = algorithm or self._default
        if algo == "gzip":
            import gzip
            return gzip.decompress(data)
        return data

    def get_algorithms(self) -> list:
        return list(self._algorithms)

    def set_default(self, algorithm: str) -> None:
        self._default = algorithm

    def ratio(self, original: bytes, compressed: bytes) -> float:
        if len(original) == 0:
            return 0.0
        return len(compressed) / len(original)
