"""Firewall — rate limiting, IP blocking, and request filtering."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from collections import defaultdict


class FirewallRule:
    __slots__ = ("name", "rule_type", "config", "active", "metadata")

    def __init__(self, name: str, rule_type: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.rule_type = rule_type
        self.config = config or {}
        self.active = True
        self.metadata: Dict[str, Any] = {}


class Firewall:
    def __init__(self) -> None:
        self._rules: Dict[str, FirewallRule] = {}
        self._blocked_ips: set = set()
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)
        self._blocked_paths: set = set()

    def add_rule(self, name: str, rule_type: str, config: Optional[Dict[str, Any]] = None) -> FirewallRule:
        rule = FirewallRule(name, rule_type, config)
        self._rules[name] = rule
        return rule

    def block_ip(self, ip: str) -> None:
        self._blocked_ips.add(ip)

    def unblock_ip(self, ip: str) -> bool:
        if ip in self._blocked_ips:
            self._blocked_ips.discard(ip)
            return True
        return False

    def is_ip_blocked(self, ip: str) -> bool:
        return ip in self._blocked_ips

    def block_path(self, path: str) -> None:
        self._blocked_paths.add(path)

    def is_path_blocked(self, path: str) -> bool:
        return path in self._blocked_paths

    def check_rate_limit(self, client_id: str, max_requests: int = 100,
                         window_seconds: float = 60.0) -> bool:
        now = time.time()
        self._rate_limits[client_id] = [
            t for t in self._rate_limits[client_id] if now - t < window_seconds
        ]
        if len(self._rate_limits[client_id]) >= max_requests:
            return False
        self._rate_limits[client_id].append(now)
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
        return [{"name": r.name, "type": r.rule_type, "active": r.active} for r in self._rules.values()]

    def stats(self) -> Dict[str, Any]:
        return {"rules": len(self._rules), "blocked_ips": len(self._blocked_ips),
                "blocked_paths": len(self._blocked_paths),
                "rate_limited_clients": len(self._rate_limits)}
