"""HealthSystem — unified health check for all layers."""
from __future__ import annotations
import time
from typing import Any, Dict, List
from enum import Enum

class HealthStatus(str, Enum):
    HEALTHY = 'healthy'; DEGRADED = 'degraded'; UNHEALTHY = 'unhealthy'

class HealthSystem:
    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}
        self._start = time.time()

    def register(self, name: str, check_fn, interval: int = 60) -> None:
        self._checks[name] = {'fn': check_fn, 'interval': interval,
                               'last_check': 0.0, 'status': HealthStatus.HEALTHY,
                               'details': {}}

    def check(self, name: str) -> Dict[str, Any]:
        info = self._checks.get(name)
        if not info: return {'name': name, 'status': HealthStatus.UNHEALTHY.value, 'error': 'not registered'}
        try:
            result = info['fn']()
            info['status'] = HealthStatus.HEALTHY if result.get('healthy', True) else HealthStatus.DEGRADED
            info['details'] = result
            info['last_check'] = time.time()
        except Exception as exc:
            info['status'] = HealthStatus.UNHEALTHY
            info['details'] = {'error': str(exc)}
        return {'name': name, 'status': info['status'].value, 'details': info['details']}

    def check_all(self) -> Dict[str, Any]:
        results = {}
        for name in self._checks:
            results[name] = self.check(name)
        statuses = [r['status'] for r in results.values()]
        overall = HealthStatus.HEALTHY
        if HealthStatus.UNHEALTHY.value in statuses:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED.value in statuses:
            overall = HealthStatus.DEGRADED
        return {'overall': overall.value, 'checks': results,
                'uptime': round(time.time() - self._start, 2),
                'total': len(results), 'healthy': sum(1 for r in results.values() if r['status'] == 'healthy')}

    def get_unhealthy(self) -> List[str]:
        return [n for n, i in self._checks.items() if i['status'] != HealthStatus.HEALTHY]
