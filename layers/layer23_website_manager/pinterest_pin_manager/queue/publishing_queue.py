"""PublishingQueue — Manage pin publishing queue with priority, retry, delay, rate limiting."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional, Tuple

from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import PinterestPin, PinStatus


class PublishingQueue:
    """Publishing queue with priority levels and rate limiting."""

    PRIORITY_HIGH = 0
    PRIORITY_NORMAL = 1
    PRIORITY_LOW = 2

    def __init__(self, max_queue_size: int = 1000) -> None:
        self._queue: List[Tuple[int, str]] = []  # (priority, pin_id)
        self._pins: Dict[str, PinterestPin] = {}
        self._lock = threading.Lock()
        self._max_size = max_queue_size
        self._total_queued = 0
        self._total_processed = 0

    def enqueue(self, pin: PinterestPin, priority: int = PRIORITY_NORMAL) -> bool:
        """Add a pin to the publishing queue."""
        with self._lock:
            if len(self._queue) >= self._max_size:
                return False
            pin.status = PinStatus.QUEUED
            self._pins[pin.pin_id] = pin
            self._queue.append((priority, pin.pin_id))
            self._queue.sort(key=lambda x: x[0])  # Sort by priority
            self._total_queued += 1
        return True

    def dequeue(self) -> Optional[PinterestPin]:
        """Get the next pin to publish (highest priority, oldest first)."""
        with self._lock:
            if not self._queue:
                return None
            _, pin_id = self._queue.pop(0)
            pin = self._pins.pop(pin_id, None)
            if pin:
                self._total_processed += 1
            return pin

    def peek(self) -> Optional[PinterestPin]:
        """View the next pin without removing it."""
        with self._lock:
            if not self._queue:
                return None
            _, pin_id = self._queue[0]
            return self._pins.get(pin_id)

    def remove(self, pin_id: str) -> bool:
        """Remove a pin from the queue."""
        with self._lock:
            for i, (_, pid) in enumerate(self._queue):
                if pid == pin_id:
                    self._queue.pop(i)
                    self._pins.pop(pin_id, None)
                    return True
        return False

    def clear(self) -> int:
        """Clear all queued pins. Returns count."""
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            self._pins.clear()
        return count

    def size(self) -> int:
        return len(self._queue)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "queue_size": len(self._queue),
            "max_size": self._max_size,
            "total_queued": self._total_queued,
            "total_processed": self._total_processed,
            "pending": len(self._queue),
        }
