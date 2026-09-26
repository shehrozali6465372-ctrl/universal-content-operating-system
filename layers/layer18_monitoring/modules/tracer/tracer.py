"""Bounded, thread-safe trace/span lifecycle tracking."""
from __future__ import annotations

import threading
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"


class Span:
    __slots__ = ("span_id", "trace_id", "parent_id", "operation", "service",
                 "start_time", "end_time", "status", "tags", "logs", "metadata")

    def __init__(self, trace_id: str, operation: str, service: str = "",
                 parent_id: Optional[str] = None) -> None:
        self.span_id = str(uuid.uuid4())
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.operation = operation
        self.service = service
        self.start_time = time.time()
        self.end_time = 0.0
        self.status = SpanStatus.OK
        self.tags: Dict[str, str] = {}
        self.logs: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

    def finish(self, status: SpanStatus = SpanStatus.OK) -> None:
        if self.end_time:
            return
        self.end_time = time.time()
        self.status = status

    def log(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.logs.append({"message": message, "data": dict(data or {}), "time": time.time()})

    def to_dict(self) -> Dict[str, Any]:
        return {"span_id": self.span_id, "trace_id": self.trace_id,
                "parent_id": self.parent_id, "operation": self.operation,
                "service": self.service, "duration_ms": round(self.duration_ms, 3),
                "status": self.status.value}


class Tracer:
    def __init__(self, max_traces: int = 1000, max_spans_per_trace: int = 1000) -> None:
        if max_traces <= 0 or max_spans_per_trace <= 0:
            raise ValueError("trace limits must be positive")
        self._lock = threading.RLock()
        self._max_traces = max_traces
        self._max_spans_per_trace = max_spans_per_trace
        self._traces: Dict[str, List[Span]] = {}
        self._spans: Dict[str, Span] = {}

    def start_trace(self, operation: str, service: str = "") -> Span:
        trace_id = str(uuid.uuid4())
        span = Span(trace_id, operation, service)
        with self._lock:
            if len(self._traces) >= self._max_traces:
                oldest = next(iter(self._traces))
                for old in self._traces.pop(oldest):
                    self._spans.pop(old.span_id, None)
            self._traces[trace_id] = [span]
            self._spans[span.span_id] = span
        return span

    def start_span(self, trace_id: str, operation: str, service: str = "",
                   parent_id: Optional[str] = None) -> Span:
        with self._lock:
            if trace_id not in self._traces:
                raise KeyError(f"unknown trace_id: {trace_id}")
            spans = self._traces[trace_id]
            if len(spans) >= self._max_spans_per_trace:
                raise RuntimeError("maximum spans per trace exceeded")
            if parent_id and parent_id not in self._spans:
                raise KeyError(f"unknown parent_id: {parent_id}")
            span = Span(trace_id, operation, service, parent_id)
            spans.append(span)
            self._spans[span.span_id] = span
            return span

    def finish_span(self, span_id: str, status: SpanStatus = SpanStatus.OK) -> bool:
        with self._lock:
            span = self._spans.get(span_id)
            if span is None:
                return False
            span.finish(status)
            return True

    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [s.to_dict() for s in self._traces.get(trace_id, [])]

    def list_traces(self) -> List[str]:
        with self._lock:
            return list(self._traces)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {"traces": len(self._traces), "spans": len(self._spans),
                    "errors": sum(s.status == SpanStatus.ERROR for s in self._spans.values())}
