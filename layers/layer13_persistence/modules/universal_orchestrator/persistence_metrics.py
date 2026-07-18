"""persistence_metrics.py — Overall persistence metrics."""
from __future__ import annotations
from typing import Any, Dict


class PersistenceMetricsAggregator:
    """Aggregates metrics from all persistence stores."""

    def __init__(self) -> None:
        self._store_metrics: Dict[str, Dict[str, Any]] = {}
        self._global_ops: int = 0
        self._global_errors: int = 0

    def record_store(self, store_name: str, ops: int = 0, errors: int = 0,
                     latency_ms: float = 0.0) -> None:
        self._store_metrics[store_name] = {"ops": ops, "errors": errors,
                                             "latency_ms": latency_ms}
        self._global_ops += ops
        self._global_errors += errors

    def get_store_metrics(self, store_name: str) -> Dict[str, Any]:
        return dict(self._store_metrics.get(store_name, {}))

    def get_global_error_rate(self) -> float:
        return self._global_errors / max(1, self._global_ops)

    def to_dict(self) -> Dict[str, Any]:
        return {"stores": len(self._store_metrics), "total_ops": self._global_ops,
                "total_errors": self._global_errors,
                "error_rate": self.get_global_error_rate()}
