"""SecurityMiddleware — rate limiting, input validation, API key management."""
from __future__ import annotations
import time
import hashlib
from typing import Any, Dict, List

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        self.max_requests = max_requests; self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}

    def allow(self, client_id: str) -> bool:
        now = time.time()
        if client_id not in self._requests:
            self._requests[client_id] = []
        self._requests[client_id] = [t for t in self._requests[client_id] if now - t < self.window_seconds]
        if len(self._requests[client_id]) >= self.max_requests:
            return False
        self._requests[client_id].append(now)
        return True

    def remaining(self, client_id: str) -> int:
        now = time.time()
        requests = [t for t in self._requests.get(client_id, []) if now - t < self.window_seconds]
        return max(0, self.max_requests - len(requests))


class InputSanitizer:
    DANGEROUS = ['eval(', 'exec(', '__import__', 'os.system', 'subprocess', 'open(']

    def sanitize(self, text: str) -> Dict[str, Any]:
        issues: List[str] = []
        for pattern in self.DANGEROUS:
            if pattern in text:
                issues.append(f'Dangerous pattern detected: {pattern}')
        if len(text) > 100000:
            issues.append('Input exceeds 100KB limit')
        return {'clean': len(issues) == 0, 'issues': issues,
                'sanitized': text if len(issues) == 0 else '[BLOCKED]'}


class APIKeyManager:
    def __init__(self) -> None:
        self._keys: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, api_key: str,
                 permissions: List[str] | None = None) -> str:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        self._keys[key_hash] = {'name': name, 'permissions': permissions or ['read'],
                                 'created': time.time(), 'active': True}
        return key_hash

    def validate(self, key_hash: str) -> Dict[str, Any]:
        key = self._keys.get(key_hash)
        if not key: return {'valid': False, 'error': 'Unknown key'}
        if not key['active']: return {'valid': False, 'error': 'Key deactivated'}
        return {'valid': True, 'name': key['name'], 'permissions': key['permissions']}

    def revoke(self, key_hash: str) -> bool:
        if key_hash in self._keys:
            self._keys[key_hash]['active'] = False; return True
        return False

    def list_keys(self) -> Dict[str, Dict[str, Any]]:
        return {k: {**v, 'key_hash': k[:8] + '...'} for k, v in self._keys.items()}


class SecurityMiddleware:
    def __init__(self) -> None:
        self.rate_limiter = RateLimiter()
        self.sanitizer = InputSanitizer()
        self.api_keys = APIKeyManager()

    def check_request(self, client_id: str, input_text: str,
                      api_key: str = '') -> Dict[str, Any]:
        issues: List[str] = []
        if not self.rate_limiter.allow(client_id):
            issues.append('Rate limit exceeded')
        sanitization = self.sanitizer.sanitize(input_text)
        if not sanitization['clean']:
            issues.extend(sanitization['issues'])
        return {'allowed': len(issues) == 0, 'issues': issues,
                'rate_limit_remaining': self.rate_limiter.remaining(client_id)}
