"""PublisherEngine — Orchestrate publishing across all platforms.

Features:
- Multi-platform publish in one call
- Platform-specific routing
- Retry with exponential backoff
- Circuit breaker pattern
- Bulk publishing
- Publish history and analytics
"""
from __future__ import annotations
import time
import threading
import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class PublishJob:
    job_id: str
    platform: str
    account_id: str
    content: str
    status: str = "pending"  # pending, processing, published, failed, retrying
    retries: int = 0
    max_retries: int = 3
    post_id: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    published_at: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "platform": self.platform,
            "account_id": self.account_id,
            "success": self.status == "published",
            "status": self.status,
            "retries": self.retries,
            "post_id": self.post_id,
            "error": self.error,
            "created_at": self.created_at,
            "published_at": self.published_at,
        }


class PublisherEngine:
    """Orchestrate publishing across all platforms."""

    def __init__(self, account_manager: Any = None, adapter: Any = None):
        self._accounts = account_manager
        self._adapter = adapter
        self._lock = threading.Lock()

        # Platform handlers (registered functions)
        self._handlers: Dict[str, Callable] = {}

        # Circuit breaker state
        self._circuit_open: Dict[str, bool] = {}
        self._circuit_failures: Dict[str, int] = {}
        self._circuit_last_failure: Dict[str, float] = {}
        self._circuit_threshold = 5
        self._circuit_reset_time = 300  # 5 minutes

        # Jobs
        self._jobs: Dict[str, PublishJob] = {}
        self._history: List[Dict[str, Any]] = []

        # Stats
        self._total_published = 0
        self._total_failed = 0
        self._total_retried = 0

    def register_handler(self, platform: str, handler: Callable) -> None:
        """Register a publish handler for a platform."""
        self._handlers[platform] = handler

    def publish(self, platform: str, account_id: str, content: str,
                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Publish content to a single platform.

        Args:
            platform: Target platform
            account_id: Account to use
            content: Content to publish
            metadata: Additional metadata

        Returns:
            Publish result dict
        """
        import hashlib
        job_id = hashlib.sha256(f"{platform}:{account_id}:{time.time()}".encode()).hexdigest()[:12]

        job = PublishJob(
            job_id=job_id,
            platform=platform,
            account_id=account_id,
            content=content,
            metadata=metadata or {},
        )

        with self._lock:
            self._jobs[job_id] = job

        # Check circuit breaker
        if self._is_circuit_open(platform):
            job.status = "failed"
            job.error = f"Circuit breaker open for {platform}"
            return job.to_dict()

        # Check account exists
        if self._accounts:
            account = self._accounts.get_account(account_id)
            if not account:
                job.status = "failed"
                job.error = f"Account {account_id} not found"
                return job.to_dict()

        # Execute publish
        job.status = "processing"
        result = self._execute_publish(job)

        # Record result
        if self._accounts:
            if result["success"]:
                self._accounts.record_post(account_id)
            else:
                self._accounts.record_error(account_id)

        return result

    def publish_multi(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Publish to multiple platforms at once.

        Each item: {"platform": str, "account_id": str, "content": str, "metadata": dict}
        """
        results = []
        for item in items:
            result = self.publish(
                platform=item["platform"],
                account_id=item["account_id"],
                content=item["content"],
                metadata=item.get("metadata", {}),
            )
            results.append(result)
        return results

    def publish_to_all(self, content: str, platforms: List[str],
                       metadata: Dict[str, Any] = None) -> Dict[str, Dict]:
        """Publish same content to multiple platforms using first available account."""
        results = {}
        for platform in platforms:
            # Find available account
            account_id = ""
            if self._accounts:
                available = self._accounts.get_available_accounts(platform)
                if available:
                    account_id = available[0].account_id

            result = self.publish(platform, account_id, content, metadata)
            results[platform] = result

        return results

    def _execute_publish(self, job: PublishJob) -> Dict[str, Any]:
        """Execute a publish job with retry logic."""
        handler = self._handlers.get(job.platform)
        if not handler:
            job.status = "failed"
            job.error = f"No handler registered for {job.platform}"
            self._record_failure(job)
            return job.to_dict()

        while job.retries <= job.max_retries:
            try:
                result = handler(job.account_id, job.content, job.metadata)
                job.status = "published"
                job.post_id = result.get("post_id", "")
                job.published_at = time.time()
                self._record_success(job)
                return job.to_dict()

            except Exception as e:
                job.retries += 1
                job.error = str(e)[:200]
                self._total_retried += 1

                if job.retries > job.max_retries:
                    job.status = "failed"
                    self._record_failure(job)
                    return job.to_dict()

                # Exponential backoff
                import time as _time
                _time.sleep(min(2 ** job.retries * 0.1, 2))

        return job.to_dict()

    def _is_circuit_open(self, platform: str) -> bool:
        """Check if circuit breaker is open."""
        if not self._circuit_open.get(platform, False):
            return False

        # Check if enough time has passed to reset
        last = self._circuit_last_failure.get(platform, 0)
        if time.time() - last > self._circuit_reset_time:
            self._circuit_open[platform] = False
            self._circuit_failures[platform] = 0
            return False

        return True

    def _record_success(self, job: PublishJob) -> None:
        """Record a successful publish."""
        with self._lock:
            self._total_published += 1
            self._circuit_failures[job.platform] = 0
            self._history.append({
                "job_id": job.job_id,
                "platform": job.platform,
                "status": "published",
                "timestamp": time.time(),
            })

    def _record_failure(self, job: PublishJob) -> None:
        """Record a failed publish and update circuit breaker."""
        with self._lock:
            self._total_failed += 1
            self._circuit_failures[job.platform] = self._circuit_failures.get(job.platform, 0) + 1
            self._circuit_last_failure[job.platform] = time.time()

            if self._circuit_failures[job.platform] >= self._circuit_threshold:
                self._circuit_open[job.platform] = True

            self._history.append({
                "job_id": job.job_id,
                "platform": job.platform,
                "status": "failed",
                "error": job.error,
                "timestamp": time.time(),
            })

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status."""
        job = self._jobs.get(job_id)
        return job.to_dict() if job else None

    def get_history(self, platform: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get publish history."""
        history = self._history
        if platform:
            history = [h for h in history if h["platform"] == platform]
        return history[-limit:]

    def get_circuit_status(self) -> Dict[str, Dict[str, Any]]:
        """Get circuit breaker status for all platforms."""
        status = {}
        for platform in set(list(self._circuit_open.keys()) + list(self._circuit_failures.keys())):
            status[platform] = {
                "open": self._circuit_open.get(platform, False),
                "failures": self._circuit_failures.get(platform, 0),
                "threshold": self._circuit_threshold,
            }
        return status

    def stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "total_published": self._total_published,
            "total_failed": self._total_failed,
            "total_retried": self._total_retried,
            "total_jobs": len(self._jobs),
            "registered_handlers": list(self._handlers.keys()),
            "circuit_breakers": self.get_circuit_status(),
        }
