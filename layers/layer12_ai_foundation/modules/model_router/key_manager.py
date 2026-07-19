"""KeyManager — intelligent API key management with health tracking.

Architecture:
    AI Brain
        │
        ▼
    Model Router          ← AI Brain ko pata nahi kaunsi key use ho rahi
        │
        ▼
    Key Manager           ← Keys ka sirf auth, health, rate limits handle kare
        │
        ▼
    Gemini API

Core Rule:
    API Keys sirf credentials hain, AI Brain ka hissa nahi.
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from enum import Enum


class KeyStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    RATE_LIMITED = "rate_limited"
    COOLDOWN = "cooldown"
    EXHAUSTED = "exhausted"
    DISABLED = "disabled"


class KeyHealth:
    """Har key ki runtime health state track kare."""

    __slots__ = (
        "key_id", "key_masked", "status", "provider",
        "requests_today", "requests_limit",
        "tokens_used", "tokens_limit",
        "rpm_remaining", "tpm_remaining",
        "last_used", "last_error", "last_error_time",
        "cooldown_until", "consecutive_errors",
        "total_requests", "total_errors",
        "avg_latency_ms", "success_rate",
        "created_at", "metadata",
    )

    def __init__(self, key_id: str, key_masked: str = "",
                 provider: str = "gemini") -> None:
        self.key_id = key_id
        self.key_masked = key_masked or f"***{key_id[-4:]}"
        self.status = KeyStatus.HEALTHY
        self.provider = provider

        # Rate limit tracking
        self.requests_today = 0
        self.requests_limit = 1000
        self.tokens_used = 0
        self.tokens_limit = 1_000_000
        self.rpm_remaining = 60
        self.tpm_remaining = 60_000

        # Timing
        self.last_used: float = 0.0
        self.last_error: str = ""
        self.last_error_time: float = 0.0
        self.cooldown_until: float = 0.0
        self.created_at = time.time()

        # Metrics
        self.consecutive_errors = 0
        self.total_requests = 0
        self.total_errors = 0
        self.avg_latency_ms = 0.0
        self.success_rate = 100.0
        self.metadata: Dict[str, Any] = {}

    @property
    def is_available(self) -> bool:
        """Key abhi use ho sakti hai?"""
        if self.status in (KeyStatus.DISABLED, KeyStatus.EXHAUSTED):
            return False
        if self.status == KeyStatus.COOLDOWN:
            if time.time() < self.cooldown_until:
                return False
            self.status = KeyStatus.HEALTHY
        if self.status == KeyStatus.RATE_LIMITED:
            if self.rpm_remaining <= 0 and time.time() < self.cooldown_until:
                return False
            self.status = KeyStatus.HEALTHY
        return True

    def record_success(self, latency_ms: float = 0.0, tokens_used: int = 0) -> None:
        """Successful request record karo."""
        self.total_requests += 1
        self.requests_today += 1
        self.tokens_used += tokens_used
        self.rpm_remaining = max(0, self.rpm_remaining - 1)
        self.tpm_remaining = max(0, self.tpm_remaining - tokens_used)
        self.last_used = time.time()
        self.consecutive_errors = 0

        # Running average latency
        n = self.total_requests
        self.avg_latency_ms = (
            (self.avg_latency_ms * (n - 1) + latency_ms) / n
        )

        self.success_rate = round(
            ((self.total_requests - self.total_errors) / max(self.total_requests, 1)) * 100, 1
        )

        # Auto-recover from degraded
        if self.status == KeyStatus.DEGRADED and self.consecutive_errors == 0:
            self.status = KeyStatus.HEALTHY

    def record_error(self, error: str, is_rate_limit: bool = False) -> None:
        """Failed request record karo."""
        self.total_requests += 1
        self.total_errors += 1
        self.last_error = error
        self.last_error_time = time.time()
        self.consecutive_errors += 1

        self.success_rate = round(
            ((self.total_requests - self.total_errors) / max(self.total_requests, 1)) * 100, 1
        )

        if is_rate_limit:
            self.status = KeyStatus.RATE_LIMITED
            self.cooldown_until = time.time() + 60
            self.rpm_remaining = 0
        elif self.consecutive_errors >= 5:
            self.status = KeyStatus.EXHAUSTED
        elif self.consecutive_errors >= 3:
            self.status = KeyStatus.DEGRADED
            self.cooldown_until = time.time() + 10
        else:
            self.status = KeyStatus.DEGRADED

    def set_cooldown(self, seconds: float) -> None:
        self.status = KeyStatus.COOLDOWN
        self.cooldown_until = time.time() + seconds

    def reset_daily(self) -> None:
        """Daily reset — naye din mein."""
        self.requests_today = 0
        self.tokens_used = 0
        self.rpm_remaining = 60
        self.tpm_remaining = 60_000
        if self.status == KeyStatus.RATE_LIMITED:
            self.status = KeyStatus.HEALTHY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "masked": self.key_masked,
            "status": self.status.value,
            "provider": self.provider,
            "requests_today": self.requests_today,
            "tokens_used": self.tokens_used,
            "rpm_remaining": self.rpm_remaining,
            "tpm_remaining": self.tpm_remaining,
            "success_rate": self.success_rate,
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "total_requests": self.total_requests,
            "consecutive_errors": self.consecutive_errors,
            "is_available": self.is_available,
        }


class KeyManager:
    """Intelligent key rotation with health-aware selection.

    AI Brain ko kabhi pata nahi kaunsi key use ho rahi hai.
    Keys sirf credentials hain, routing logic KeyManager ki hai.
    """

    def __init__(self) -> None:
        self._keys: Dict[str, KeyHealth] = {}
        self._actual_keys: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._history: List[Dict[str, Any]] = []
        self._strategy = "healthiest"  # healthiest, round_robin, least_used, cost_optimized
        self._round_robin_index = 0

    def register_key(self, key_id: str, actual_key: str,
                     provider: str = "gemini",
                     requests_limit: int = 1000,
                     tokens_limit: int = 1_000_000) -> KeyHealth:
        """Naya key register karo (actual key sirf yahan store hoti hai)."""
        masked = f"***{actual_key[-6:]}" if len(actual_key) > 6 else "***"
        health = KeyHealth(key_id, masked, provider)
        health.requests_limit = requests_limit
        health.tokens_limit = tokens_limit
        with self._lock:
            self._keys[key_id] = health
            self._actual_keys[key_id] = actual_key
        return health

    def unregister_key(self, key_id: str) -> bool:
        with self._lock:
            if key_id in self._keys:
                del self._keys[key_id]
                self._actual_keys.pop(key_id, None)
                return True
        return False

    def set_strategy(self, strategy: str) -> None:
        """Rotation strategy set karo: healthiest, round_robin, least_used, cost_optimized"""
        valid = ["healthiest", "round_robin", "least_used", "cost_optimized"]
        if strategy in valid:
            self._strategy = strategy

    def select_key(self, capability: str = "text") -> Optional[str]:
        """Best available key select karo (actual key return hoti hai)."""
        with self._lock:
            available = [
                kid for kid, kh in self._keys.items()
                if kh.is_available and kid in self._actual_keys
            ]
            if not available:
                return None

            if self._strategy == "healthiest":
                best = max(available, key=lambda k: self._keys[k].success_rate)
            elif self._strategy == "round_robin":
                best = available[self._round_robin_index % len(available)]
                self._round_robin_index += 1
            elif self._strategy == "least_used":
                best = min(available, key=lambda k: self._keys[k].total_requests)
            else:
                best = available[0]

            self._keys[best].record_success(0, 0)
            return self._actual_keys.get(best)

    def select_healthiest_key(self) -> Optional[str]:
        """Sab se healthy key return karo (actual key)."""
        with self._lock:
            available = {
                kid: kh for kid, kh in self._keys.items()
                if kh.is_available and kid in self._actual_keys
            }
            if not available:
                return None
            best_id = max(available, key=lambda k: available[k].success_rate)
            return self._actual_keys.get(best_id)

    def report_success(self, key_id: str, latency_ms: float = 0.0,
                       tokens_used: int = 0) -> None:
        """Request success report karo."""
        with self._lock:
            if key_id in self._keys:
                self._keys[key_id].record_success(latency_ms, tokens_used)
                self._history.append({
                    "key_id": key_id, "event": "success",
                    "latency_ms": latency_ms, "time": time.time()})

    def report_error(self, key_id: str, error: str,
                     is_rate_limit: bool = False) -> None:
        """Request failure report karo."""
        with self._lock:
            if key_id in self._keys:
                self._keys[key_id].record_error(error, is_rate_limit)
                self._history.append({
                    "key_id": key_id, "event": "error",
                    "error": error, "time": time.time()})

    def force_cooldown(self, key_id: str, seconds: float = 60.0) -> bool:
        with self._lock:
            if key_id in self._keys:
                self._keys[key_id].set_cooldown(seconds)
                return True
        return False

    def reset_daily(self) -> None:
        with self._lock:
            for kh in self._keys.values():
                kh.reset_daily()

    def get_key_health(self, key_id: str) -> Optional[Dict[str, Any]]:
        kh = self._keys.get(key_id)
        return kh.to_dict() if kh else None

    def get_all_health(self) -> List[Dict[str, Any]]:
        return [kh.to_dict() for kh in self._keys.values()]

    def get_healthy_keys(self) -> List[str]:
        return [kid for kid, kh in self._keys.items() if kh.is_available]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._keys)
        healthy = sum(1 for kh in self._keys.values() if kh.status == KeyStatus.HEALTHY)
        available = sum(1 for kh in self._keys.values() if kh.is_available)
        total_requests = sum(kh.total_requests for kh in self._keys.values())
        total_errors = sum(kh.total_errors for kh in self._keys.values())
        return {
            "total_keys": total,
            "healthy": healthy,
            "available": available,
            "strategy": self._strategy,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "overall_success_rate": round(
                ((total_requests - total_errors) / max(total_requests, 1)) * 100, 1
            ),
        }

    def list_keys(self) -> List[Dict[str, Any]]:
        return [kh.to_dict() for kh in self._keys.values()]

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history[-limit:]
