"""Orchestration Context — Global execution context for requests."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict

_OC_COUNTER = itertools.count(1)


class OrchestrationContext:
    """Stores execution state for a single orchestration request."""

    __slots__ = ("request_id", "session_id", "user_id", "workflow_state",
                 "current_layer", "metadata", "timestamps", "layer_outputs",
                 "errors")

    def __init__(self, user_id: str = "", session_id: str = "") -> None:
        self.request_id: str = f"req_{next(_OC_COUNTER)}"
        self.session_id = session_id or f"sess_{next(_OC_COUNTER)}"
        self.user_id = user_id
        self.workflow_state: str = "created"
        self.current_layer: str = ""
        self.metadata: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {"created": time.time()}
        self.layer_outputs: Dict[str, Any] = {}
        self.errors: list = []

    def update_state(self, state: str) -> None:
        self.workflow_state = state
        self.timestamps[state] = time.time()

    def set_layer(self, layer: str) -> None:
        self.current_layer = layer
        self.timestamps[f"layer_{layer}_start"] = time.time()

    def complete_layer(self, layer: str, output: Any = None) -> None:
        self.layer_outputs[layer] = output
        self.timestamps[f"layer_{layer}_end"] = time.time()

    def add_error(self, layer: str, error: str) -> None:
        self.errors.append({"layer": layer, "error": error, "timestamp": time.time()})

    def clone(self) -> "OrchestrationContext":
        ctx = OrchestrationContext(self.user_id, self.session_id)
        ctx.request_id = self.request_id
        ctx.workflow_state = self.workflow_state
        ctx.current_layer = self.current_layer
        ctx.metadata = dict(self.metadata)
        ctx.timestamps = dict(self.timestamps)
        ctx.layer_outputs = dict(self.layer_outputs)
        ctx.errors = list(self.errors)
        return ctx

    def clear(self) -> None:
        self.workflow_state = "created"
        self.current_layer = ""
        self.metadata.clear()
        self.layer_outputs.clear()
        self.errors.clear()
        self.timestamps = {"created": time.time()}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "workflow_state": self.workflow_state,
            "current_layer": self.current_layer,
            "layers_completed": list(self.layer_outputs.keys()),
            "error_count": len(self.errors),
        }
