"""PinPublisher — Publish pins to correct account, board, with retry logic."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import PinterestPin, PinStatus
from layers.layer23_website_manager.pinterest_pin_manager.exceptions import (
    PublishFailedError, RateLimitError, PinterestAPIError,
)


class PinPublisher:
    """Publish pins to Pinterest — selects account, board, handles retries."""

    def __init__(self) -> None:
        self._publish_log: List[dict] = []
        self._lock = threading.Lock()
        self._total_published = 0
        self._total_failed = 0
        self._rate_limit_remaining = 1000
        self._rate_limit_reset = 0.0

    def publish(self, pin: PinterestPin) -> Dict[str, Any]:
        """Publish a pin through a configured real Pinterest API provider.

        This repository currently has no verified Pinterest API transport in this
        publisher. Never simulate a successful publication.
        """
        raise NotImplementedError(
            "Real Pinterest API publishing is not configured; simulated publication is disabled"
        )

    def publish_batch(self, pins: List[PinterestPin]) -> List[Dict[str, Any]]:
        """Publish multiple pins."""
        results = []
        for pin in pins:
            try:
                results.append(self.publish(pin))
            except Exception as e:
                with self._lock:
                    pin.status = PinStatus.FAILED
                    pin.last_error = str(e)[:200]
                    pin.retry_count += 1
                    self._total_failed += 1
                results.append({"pin_id": pin.pin_id, "status": "failed", "error": str(e)})
        return results

    def retry_pin(self, pin: PinterestPin) -> Optional[Dict[str, Any]]:
        """Retry a failed pin."""
        if not pin.can_retry:
            return None

        with self._lock:
            pin.retry_count += 1
            pin.status = PinStatus.DRAFT  # Reset for retry
        return self.publish(pin)

    def check_rate_limit(self) -> Dict[str, Any]:
        return {
            "remaining": self._rate_limit_remaining,
            "reset_at": self._rate_limit_reset,
            "is_limited": self._rate_limit_remaining == 0,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_published": self._total_published,
            "total_failed": self._total_failed,
            "success_rate": round(
                (self._total_published / max(self._total_published + self._total_failed, 1)) * 100, 1
            ),
            "total_attempts": len(self._publish_log),
        }
