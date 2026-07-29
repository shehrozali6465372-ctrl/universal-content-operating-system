"""PinterestTrafficTracker — Track pin clicks, board clicks, account traffic, saves."""
from __future__ import annotations
import time
import threading
import random
from typing import Any, Dict, List, Optional


class PinterestTrafficTracker:
    """Track Pinterest-specific traffic — per pin, per board, per account."""

    def __init__(self) -> None:
        self._pin_clicks: Dict[str, int] = {}
        self._board_clicks: Dict[str, int] = {}
        self._account_clicks: Dict[str, int] = {}
        self._saves: Dict[str, int] = {}
        self._outbound: Dict[str, int] = {}
        self._lock = threading.Lock()

    def record_pin_click(self, pin_id: str, board_id: str = "", account_id: str = "") -> None:
        with self._lock:
            self._pin_clicks[pin_id] = self._pin_clicks.get(pin_id, 0) + 1
            if board_id: self._board_clicks[board_id] = self._board_clicks.get(board_id, 0) + 1
            if account_id: self._account_clicks[account_id] = self._account_clicks.get(account_id, 0) + 1

    def record_save(self, pin_id: str) -> None:
        with self._lock: self._saves[pin_id] = self._saves.get(pin_id, 0) + 1

    def record_outbound_click(self, pin_id: str) -> None:
        with self._lock: self._outbound[pin_id] = self._outbound.get(pin_id, 0) + 1

    def get_pin_traffic(self, pin_id: str) -> Dict[str, int]:
        return {"clicks": self._pin_clicks.get(pin_id, 0), "saves": self._saves.get(pin_id, 0),
                "outbound": self._outbound.get(pin_id, 0)}

    def get_top_pins(self, top_k: int = 5) -> List[tuple]:
        return sorted(self._pin_clicks.items(), key=lambda x: x[1], reverse=True)[:top_k]

    def simulate_activity(self, pin_count: int = 5, days: int = 7) -> int:
        total = 0
        for d in range(days):
            for p in range(pin_count):
                pid = f"pin_{p}"
                bid = f"board_{p % 3}"
                aid = f"acc_{(p % 2) + 1}"
                for _ in range(random.randint(1, 10)):
                    self.record_pin_click(pid, bid, aid)
                    total += 1
                if random.random() > 0.5:
                    self.record_save(pid)
                    self.record_outbound_click(pid)
        return total

    def get_stats(self) -> Dict[str, Any]:
        return {"total_pin_clicks": sum(self._pin_clicks.values()), "unique_pins": len(self._pin_clicks),
                "total_saves": sum(self._saves.values()), "total_boards": len(self._board_clicks)}
