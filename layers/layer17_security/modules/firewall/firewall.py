"""Thread-safe request firewall primitives."""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional


class FirewallRule:
    __slots__ = ("name", "rule_type", "config", "active", "metadata")

    def __init__(self, name: str, rule_type: str,
                 config: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.rule_type = rule_type
        self.config = dict(config or {})
        self.active = True
        self.metadata: Dict[str, Any] = {}


class Firewall:
    def __init__(self, max_clients: int = 10000) -> None:
        if max_clients <= 0:
            raise ValueError("max_clients must be positive")
        self._rules: Dict[str, FirewallRule] = {}
        self._blocked_ips: set[str] = set()
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)
        self._blocked_paths: set[str] = set()
        self._max_clients = max_clients
        self._lock = threading.RLock()

    def add_rule(self, name: str, rule_type: str,
                 config: Optional[Dict[str, Any]] = None) -> FirewallRule:
        if not name:
            raise ValueError("rule name is required")
        with self._lock:
            rule = FirewallRule(name, rule_type, config)
            self._rules[name] = rule
            return rule

    def block_ip(self, ip: str) -> None:
        with self._lock:
            self._blocked_ips.add(ip)

    def unblock_ip(self, ip: str) -> bool:
        with self._lock:
            return self._blocked_ips.discard(ip) is None and ip not in self._blocked_ips

    def is_ip_blocked(self, ip: str) -> bool:
        with self._lock:
            return ip in self._blocked_ips

    def block_path(self, path: str) -> None:
        with self._lock:
            self._blocked_paths.add(path)

    def is_path_blocked(self, path: str) -> bool:
        with self._lock:
            return path in self._blocked_paths

    def check_rate_limit(self, client_id: str, max_requests: int = 100,
                         window_seconds: float = 60.0) -> bool:
        if not client_id or max_requests <= 0 or window_seconds <= 0:
            return False
        now = time.monotonic()
        with self._lock:
            timestamps = self._rate_limits[client_id]
            timestamps[:] = [t for t in timestamps if now - t < window_seconds]
            if len(timestamps) >= max_requests:
                return False
            timestamps.append(now)
            if len(self._rate_limits) > self._max_clients:
                oldest = min(self._rate_limits, key=lambda key: self._rate_limits[key][-1])
                self._rate_limits.pop(oldest, None)
            return True

    def evaluate(self, ip: str, path: str, client_id: str = "") -> Dict[str, Any]:
        if self.is_ip_blocked(ip):
            return {"allowed": False, "reason": "ip_blocked"}
        if self.is_path_blocked(path):
            return {"allowed": False, "reason": "path_blocked"}
        if client_id and not self.check_rate_limit(client_id):
            return {"allowed": False, "reason": "rate_limited"}
        return {"allowed": True}

    def list_rules(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [{"name": r.name, "type": r.rule_type, "active": r.active}
                    for r in self._rules.values()]

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {"rules": len(self._rules), "blocked_ips": len(self._blocked_ips),
                    "blocked_paths": len(self._blocked_paths),
                    "rate_limited_clients": len(self._rate_limits)}
