"""Tracer — distributed request tracing across layers."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from enum import Enum


class SpanStatus(str, Enum):
    OK = "ok"; ERROR = "error"; TIMEOUT = "timeout"


class Span:
    __slots__ = ("span_id", "trace_id", "parent_id", "operation",
                 "service", "start_time", "end_time", "status",
                 "tags", "logs", "metadata")

    def __init__(self, trace_id: str, operation: str, service: str = "",
                 parent_id: Optional[str] = None) -> None:
        self.span_id = str(uuid.uuid4())[:8]
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.operation = operation
        self.service = service
        self.start_time = time.time()
        self.end_time: float = 0.0
        self.status = SpanStatus.OK
        self.tags: Dict[str, str] = {}
        self.logs: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    def finish(self, status: SpanStatus = SpanStatus.OK) -> None:
        self.end_time = time.time()
        self.status = status

    def log(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.logs.append({"message": message, "data": data, "time": time.time()})

    def to_dict(self) -> Dict[str, Any]:
        return {"span_id": self.span_id, "trace_id": self.trace_id,
                "operation": self.operation, "service": self.service,
                "duration_ms": round(self.duration_ms, 3),
                "status": self.status.value}


class Tracer:
    def __init__(self) -> None:
        self._traces: Dict[str, List[Span]] = {}
        self._spans: Dict[str, Span] = {}

    def start_trace(self, operation: str, service: str = "") -> Span:
        trace_id = str(uuid.uuid4())[:12]
        span = Span(trace_id, operation, service)
        self._traces[trace_id] = [span]
        self._spans[span.span_id] = span
        return span

    def start_span(self, trace_id: str, operation: str, service: str = "",
                   parent_id: Optional[str] = None) -> Optional[Span]:
        span = Span(trace_id, operation, service, parent_id)
        self._traces.setdefault(trace_id, []).append(span)
        self._spans[span.span_id] = span
        return span

    def finish_span(self, span_id: str, status: SpanStatus = SpanStatus.OK) -> bool:
        span = self._spans.get(span_id)
        if span:
            span.finish(status)
            return True
        return False

    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        spans = self._traces.get(trace_id, [])
        return [s.to_dict() for s in spans]

    def list_traces(self) -> List[str]:
        return list(self._traces.keys())

    def stats(self) -> Dict[str, Any]:
        total_spans = len(self._spans)
        errors = sum(1 for s in self._spans.values() if s.status == SpanStatus.ERROR)
        return {"traces": len(self._traces), "spans": total_spans, "errors": errors}
