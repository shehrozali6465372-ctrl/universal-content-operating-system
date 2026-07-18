"""sequence_manager.py — Database sequence management."""
from __future__ import annotations
from typing import Dict, Optional


class DatabaseSequence:
    """Database sequence."""
    __slots__ = ("name", "current_value", "increment", "min_value", "max_value")
    _counter = 0

    def __init__(self, name: str, start: int = 1, increment: int = 1) -> None:
        DatabaseSequence._counter += 1
        self.name = name
        self.current_value: int = start
        self.increment = increment
        self.min_value: int = 1
        self.max_value: int = 2147483647

    def next_value(self) -> int:
        val = self.current_value
        self.current_value += self.increment
        if self.current_value > self.max_value:
            self.current_value = self.min_value
        return val


class SequenceManager:
    """Manages database sequences."""

    def __init__(self) -> None:
        self._sequences: Dict[str, DatabaseSequence] = {}

    def create(self, name: str, start: int = 1, increment: int = 1) -> DatabaseSequence:
        seq = DatabaseSequence(name, start, increment)
        self._sequences[name] = seq
        return seq

    def next_value(self, name: str) -> Optional[int]:
        seq = self._sequences.get(name)
        return seq.next_value() if seq else None

    def get(self, name: str) -> Optional[DatabaseSequence]:
        return self._sequences.get(name)

    def list_all(self) -> Dict[str, DatabaseSequence]:
        return dict(self._sequences)
