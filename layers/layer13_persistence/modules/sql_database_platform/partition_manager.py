"""partition_manager.py — Table partitioning."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class Partition:
    """Table partition definition."""
    __slots__ = ("partition_name", "table_name", "partition_type", "column",
                 "range_start", "range_end", "created_at")

    def __init__(self, name: str, table_name: str, partition_type: str = "range",
                 column: str = "") -> None:
        self.partition_name = name
        self.table_name = table_name
        self.partition_type = partition_type
        self.column = column
        self.range_start: str = ""
        self.range_end: str = ""
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.partition_name, "table": self.table_name,
                "type": self.partition_type, "column": self.column}


class PartitionManager:
    """Manages table partitioning."""

    def __init__(self) -> None:
        self._partitions: Dict[str, Partition] = {}

    def create_partition(self, partition: Partition) -> bool:
        self._partitions[partition.partition_name] = partition
        return True

    def drop_partition(self, name: str) -> bool:
        return self._partitions.pop(name, None) is not None

    def get_partitions_for_table(self, table: str) -> List[Partition]:
        return [p for p in self._partitions.values() if p.table_name == table]

    def list_all(self) -> List[Partition]:
        return list(self._partitions.values())

    def stats(self) -> Dict[str, Any]:
        tables = {}
        for p in self._partitions.values():
            tables[p.table_name] = tables.get(p.table_name, 0) + 1
        return {"total": len(self._partitions), "by_table": tables}
