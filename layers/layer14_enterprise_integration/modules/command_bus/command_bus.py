"""CommandBus — dispatch commands to registered handlers across layers."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, List, Optional


class Command:
    __slots__ = ("command_id", "name", "payload", "source", "timestamp", "metadata")

    def __init__(self, name: str, payload: Optional[Dict[str, Any]] = None,
                 source: str = "") -> None:
        self.command_id = str(uuid.uuid4())[:12]
        self.name = name
        self.payload = payload or {}
        self.source = source
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"command_id": self.command_id, "name": self.name,
                "payload": self.payload, "source": self.source,
                "timestamp": self.timestamp}


class CommandResult:
    __slots__ = ("command_id", "success", "result", "error", "duration_ms")

    def __init__(self, command_id: str) -> None:
        self.command_id = command_id
        self.success = False
        self.result: Any = None
        self.error: Optional[str] = None
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"command_id": self.command_id, "success": self.success,
                "error": self.error, "duration_ms": round(self.duration_ms, 2)}


class CommandBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._history: List[Dict[str, Any]] = []

    def register(self, command_name: str, handler: Callable) -> None:
        if command_name not in self._handlers:
            self._handlers[command_name] = []
        self._handlers[command_name].append(handler)

    def unregister(self, command_name: str, handler: Optional[Callable] = None) -> bool:
        if command_name not in self._handlers:
            return False
        if handler:
            self._handlers[command_name] = [h for h in self._handlers[command_name] if h != handler]
            return True
        del self._handlers[command_name]
        return True

    def dispatch(self, name: str, payload: Optional[Dict[str, Any]] = None,
                 source: str = "") -> CommandResult:
        cmd = Command(name, payload, source)
        result = CommandResult(cmd.command_id)
        handlers = self._handlers.get(name, [])
        if not handlers:
            result.error = "no_handler_registered"
            self._history.append({**cmd.to_dict(), "result": result.to_dict()})
            return result
        start = time.time()
        try:
            outputs = []
            for handler in handlers:
                outputs.append(handler(cmd.payload))
            result.success = True
            result.result = outputs[0] if len(outputs) == 1 else outputs
        except Exception as exc:
            result.error = str(exc)
        result.duration_ms = (time.time() - start) * 1000
        self._history.append({**cmd.to_dict(), "result": result.to_dict()})
        return result

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def list_commands(self) -> List[str]:
        return list(self._handlers.keys())

    def clear_history(self) -> None:
        self._history.clear()
