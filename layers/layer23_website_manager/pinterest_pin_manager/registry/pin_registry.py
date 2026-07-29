"""PinRegistry — CRUD for Pinterest Pins across all accounts and boards."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import (
    PinterestPin, PinStatus, PinType,
)
from layers.layer23_website_manager.pinterest_pin_manager.exceptions import (
    PinNotFoundError, DuplicatePinError, PinLimitError, InvalidPinTitleError,
)


class PinRegistry:
    """Register, update, delete, archive, restore pins with multi-account support."""

    def __init__(self) -> None:
        self._pins: Dict[str, PinterestPin] = {}
        self._lock = threading.Lock()
        self._total_created = 0

    def create(self, pin_title: str, account_id: str = "", board_id: str = "",
                description: str = "", website_url: str = "",
                image_path: str = "", niche: str = "",
                keywords: Optional[List[str]] = None,
                hashtags: Optional[List[str]] = None) -> PinterestPin:
        """Create a new pin."""
        if not pin_title or not pin_title.strip():
            raise InvalidPinTitleError("Pin title cannot be empty")

        # Duplicate check by title+board
        for pin in self._pins.values():
            if pin.board_id == board_id and pin.pin_title.lower() == pin_title.lower():
                if pin.status != PinStatus.ARCHIVED:
                    raise DuplicatePinError(f"Pin '{pin_title}' already exists in this board")

        pin = PinterestPin(
            account_id=account_id,
            board_id=board_id,
            pin_title=pin_title,
            pin_description=description,
            website_url=website_url,
            image_path=image_path,
            niche=niche,
            seo_keywords=keywords or [],
            hashtags=hashtags or [],
        )

        # Auto SEO title
        pin.seo_title = pin_title

        with self._lock:
            self._pins[pin.pin_id] = pin
            self._total_created += 1

        return pin

    def get(self, pin_id: str) -> Optional[PinterestPin]:
        return self._pins.get(pin_id)

    def update(self, pin_id: str, **kwargs) -> Optional[PinterestPin]:
        pin = self._pins.get(pin_id)
        if not pin:
            return None

        allowed = {"pin_title", "pin_description", "alt_text", "call_to_action",
                    "image_path", "image_url", "seo_title", "seo_description",
                    "seo_keywords", "hashtags", "website_url", "affiliate_url",
                    "board_id", "account_id", "search_intent", "note",
                    "image_width", "image_height", "rich_pin_data", "rich_pin_type"}

        with self._lock:
            for key, value in kwargs.items():
                if key in allowed:
                    setattr(pin, key, value)
            pin.updated_at = time.time()

        return pin

    def delete(self, pin_id: str) -> bool:
        with self._lock:
            return self._pins.pop(pin_id, None) is not None

    def set_status(self, pin_id: str, status: PinStatus) -> Optional[PinterestPin]:
        pin = self._pins.get(pin_id)
        if not pin:
            return None
        with self._lock:
            pin.status = status
            if status == PinStatus.PUBLISHED:
                pin.published_at = time.time()
            pin.updated_at = time.time()
        return pin

    def archive(self, pin_id: str) -> Optional[PinterestPin]:
        return self.set_status(pin_id, PinStatus.ARCHIVED)

    def get_by_board(self, board_id: str, status: Optional[PinStatus] = None) -> List[PinterestPin]:
        pins = [p for p in self._pins.values() if p.board_id == board_id]
        if status:
            pins = [p for p in pins if p.status == status]
        return sorted(pins, key=lambda p: p.created_at, reverse=True)

    def get_by_account(self, account_id: str, status: Optional[PinStatus] = None) -> List[PinterestPin]:
        pins = [p for p in self._pins.values() if p.account_id == account_id]
        if status:
            pins = [p for p in pins if p.status == status]
        return sorted(pins, key=lambda p: p.created_at, reverse=True)

    def get_by_niche(self, niche: str) -> List[PinterestPin]:
        return [p for p in self._pins.values() if p.niche == niche and p.status != PinStatus.ARCHIVED]

    def get_all(self, status: Optional[PinStatus] = None) -> List[PinterestPin]:
        pins = list(self._pins.values())
        if status:
            pins = [p for p in pins if p.status == status]
        return sorted(pins, key=lambda p: p.created_at, reverse=True)

    def count_by_board(self, board_id: str) -> int:
        return sum(1 for p in self._pins.values() if p.board_id == board_id)

    def get_stats(self) -> Dict[str, Any]:
        by_status: Dict[str, int] = {}
        for p in self._pins.values():
            by_status[p.status.value] = by_status.get(p.status.value, 0) + 1
        return {
            "total_pins": len(self._pins),
            "by_status": by_status,
            "total_created": self._total_created,
            "published": by_status.get("published", 0),
            "draft": by_status.get("draft", 0),
            "scheduled": by_status.get("scheduled", 0),
            "failed": by_status.get("failed", 0),
        }
