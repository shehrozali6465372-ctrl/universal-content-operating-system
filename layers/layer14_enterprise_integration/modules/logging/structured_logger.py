"""StructuredLogger — JSON-based structured logging for all layers."""
from __future__ import annotations
import json
import time
import sys
from typing import Any, Dict, List, Optional
from enum import IntEnum

class LogLevel(IntEnum):
    DEBUG = 0; INFO = 1; WARNING = 2; ERROR = 3; CRITICAL = 4

_LEVEL_NAMES = {0: 'DEBUG', 1: 'INFO', 2: 'WARNING', 3: 'ERROR', 4: 'CRITICAL'}

class StructuredLogger:
    def __init__(self, name: str = 'aios', level: LogLevel = LogLevel.INFO,
                 output_file: Optional[str] = None) -> None:
        self.name = name; self.level = level; self.output_file = output_file
        self._log: List[Dict[str, Any]] = []

    def _log_entry(self, level: LogLevel, message: str,
                   data: Optional[Dict[str, Any]] = None,
                   layer: str = '', module: str = '') -> None:
        if level < self.level: return
        entry = {'timestamp': time.time(), 'level': _LEVEL_NAMES[level], 'logger': self.name,
                 'message': message, 'layer': layer, 'module': module, 'data': data or {}}
        self._log.append(entry)
        print(json.dumps(entry, default=str), file=sys.stderr)
        if self.output_file:
            try:
                with open(self.output_file, 'a') as f:
                    f.write(json.dumps(entry, default=str) + '\n')
            except Exception: pass

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log_entry(LogLevel.DEBUG, msg, **kwargs)
    def info(self, msg: str, **kwargs: Any) -> None:
        self._log_entry(LogLevel.INFO, msg, **kwargs)
    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log_entry(LogLevel.WARNING, msg, **kwargs)
    def error(self, msg: str, **kwargs: Any) -> None:
        self._log_entry(LogLevel.ERROR, msg, **kwargs)
    def critical(self, msg: str, **kwargs: Any) -> None:
        self._log_entry(LogLevel.CRITICAL, msg, **kwargs)

    def get_logs(self, level: Optional[LogLevel] = None,
                 layer: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self._log
        if level is not None:
            target = _LEVEL_NAMES[level]
            results = [e for e in results if e['level'] == target]
        if layer: results = [e for e in results if e['layer'] == layer]
        return results

    def count(self) -> int:
        return len(self._log)

    def clear(self) -> None:
        self._log.clear()
