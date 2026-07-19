"""LogManager — manage loggers across all layers."""
from __future__ import annotations
from typing import Dict, Optional
from .structured_logger import StructuredLogger, LogLevel

class LogManager:
    _instance: Optional['LogManager'] = None

    def __new__(cls) -> 'LogManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loggers: Dict[str, StructuredLogger] = {}
        return cls._instance

    def get_logger(self, name: str, layer: str = '') -> StructuredLogger:
        if name not in self._loggers:
            self._loggers[name] = StructuredLogger(name=name, level=LogLevel.INFO)
        if layer:
            self._loggers[name].layer = layer
        return self._loggers[name]

    def register(self, name: str, logger: StructuredLogger) -> None:
        self._loggers[name] = logger

    def list_loggers(self) -> Dict[str, str]:
        return {n: str(l.level) for n, l in self._loggers.items()}

    def set_level(self, name: str, level: LogLevel) -> bool:
        if name in self._loggers:
            self._loggers[name].level = level; return True
        return False

    def count(self) -> int:
        return len(self._loggers)
