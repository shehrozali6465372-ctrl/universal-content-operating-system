"""PinterestPinManager — Layer 23 / Module 4.

Complete Pinterest Pin lifecycle: AI generation, SEO, image management,
scheduling, publishing, analytics, health, and optimization.

Flow: Article → AI Builder → SEO → Image → Link → Schedule → Publish → Analytics
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import (
    PinterestPin, PinStatus, PinType,
)
from layers.layer23_website_manager.pinterest_pin_manager.models.pin_analytics import PinAnalytics
from layers.layer23_website_manager.pinterest_pin_manager.registry.pin_registry import PinRegistry
from layers.layer23_website_manager.pinterest_pin_manager.builder.ai_pin_builder import AIPinBuilder
from layers.layer23_website_manager.pinterest_pin_manager.images.pin_image_manager import PinImageManager
from layers.layer23_website_manager.pinterest_pin_manager.seo.pin_seo_manager import PinSEOManager
from layers.layer23_website_manager.pinterest_pin_manager.links.website_link_manager import WebsiteLinkManager
from layers.layer23_website_manager.pinterest_pin_manager.links.rich_pin_manager import RichPinManager
from layers.layer23_website_manager.pinterest_pin_manager.scheduler.pin_scheduler import PinScheduler
from layers.layer23_website_manager.pinterest_pin_manager.publisher.pin_publisher import PinPublisher
from layers.layer23_website_manager.pinterest_pin_manager.queue.publishing_queue import PublishingQueue
from layers.layer23_website_manager.pinterest_pin_manager.analytics.pin_analytics_tracker import PinAnalyticsTracker
from layers.layer23_website_manager.pinterest_pin_manager.health.pin_health import PinHealthChecker
from layers.layer23_website_manager.pinterest_pin_manager.optimizer.pin_optimizer import PinOptimizer


class PinterestPinManager:
    """Primary facade for Pinterest Pin Management.

    Full pipeline: Article → AI Builder → SEO → Image → Link → Schedule → Publish → Analytics
    Coordinates 12 sub-modules for end-to-end pin lifecycle.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()

        # Sub-modules
        self.registry = PinRegistry()
        self.builder = AIPinBuilder()
        self.images = PinImageManager()
        self.seo = PinSEOManager()
        self.links = WebsiteLinkManager()
        self.rich_pins = RichPinManager()
        self.scheduler = PinScheduler()
        self.publisher = PinPublisher()
        self.queue = PublishingQueue()
        self.analytics = PinAnalyticsTracker()
        self.health = PinHealthChecker()
        self.optimizer = PinOptimizer()

        self._total_operations = 0

    # ─── Full Pipeline ────────────────────────────────────

    def create_pin_from_article(self, article_title: str, article_content: str = "",
                                 article_id: str = "", website_url: str = "",
                                 account_id: str = "", board_id: str = "",
                                 niche: str = "", keywords: Optional[List[str]] = None,
                                 image_path: str = "", author: str = "",
                                 site_name: str = "") -> PinterestPin:
        """Full pipeline: Article → AI Builder → SEO → Link → Rich Pin → Registry."""
        pin = self.registry.create(
            pin_title=article_title[:100],
            description=article_content[:500],
            website_url=website_url,
            account_id=account_id,
            board_id=board_id,
            niche=niche,
            keywords=keywords or [],
            image_path=image_path,
        )
        pin.article_id = article_id

        # Step 1: AI Build content
        ai_content = self.builder.build_from_article(
            article_title, article_content, niche, keywords or []
        )
        pin.pin_title = ai_content["pin_title"]
        pin.pin_description = ai_content["pin_description"]
        pin.alt_text = ai_content["alt_text"]
        pin.call_to_action = ai_content["call_to_action"]
        pin.hashtags = ai_content["hashtags"]
        pin.seo_keywords = ai_content["seo_keywords"]
        pin.search_intent = ai_content["search_intent"]
        pin.is_ai_generated = True

        # Step 2: SEO optimization
        self.seo.optimize_pin(pin)

        # Step 3: Website link
        if website_url:
            self.links.attach_article_link(pin, website_url, article_title)

        # Step 4: Rich pin metadata
        self.rich_pins.create_article_rich_pin(
            pin, title=article_title, author=author, site_name=site_name, url=website_url,
        )

        # Step 5: Validate image
        if image_path:
            self.images.validate_image(image_path)

        self._log("create_pin_from_article", {"article": article_title})
        return pin

    # ─── Pin CRUD ─────────────────────────────────────────

    def create_pin(self, pin_title: str, account_id: str = "", board_id: str = "",
                    description: str = "", website_url: str = "",
                    image_path: str = "", niche: str = "",
                    keywords: Optional[List[str]] = None) -> PinterestPin:
        pin = self.registry.create(
            pin_title=pin_title, account_id=account_id, board_id=board_id,
            description=description, website_url=website_url,
            image_path=image_path, niche=niche, keywords=keywords,
        )
        self.seo.optimize_pin(pin)
        self._log("create_pin", {"pin_title": pin_title})
        return pin

    def get_pin(self, pin_id: str) -> Optional[PinterestPin]:
        return self.registry.get(pin_id)

    def update_pin(self, pin_id: str, **kwargs) -> Optional[PinterestPin]:
        result = self.registry.update(pin_id, **kwargs)
        if result:
            self._log("update_pin", {"pin_id": pin_id})
        return result

    def delete_pin(self, pin_id: str) -> bool:
        result = self.registry.delete(pin_id)
        if result:
            self._log("delete_pin", {"pin_id": pin_id})
        return result

    def archive_pin(self, pin_id: str) -> Optional[PinterestPin]:
        return self.registry.archive(pin_id)

    # ─── Scheduling & Publishing ──────────────────────────

    def schedule_pin(self, pin_id: str, publish_time: float) -> bool:
        pin = self.registry.get(pin_id)
        if not pin:
            return False
        return self.scheduler.schedule(pin, publish_time)

    def publish_pin(self, pin_id: str) -> Dict[str, Any]:
        pin = self.registry.get(pin_id)
        if not pin:
            return {"error": "Pin not found"}
        return self.publisher.publish(pin)

    def queue_pin(self, pin_id: str, priority: int = 1) -> bool:
        pin = self.registry.get(pin_id)
        if not pin:
            return False
        return self.queue.enqueue(pin, priority)

    def process_queue(self) -> int:
        """Process all queued pins. Returns count published."""
        count = 0
        while True:
            pin = self.queue.dequeue()
            if not pin:
                break
            try:
                self.publisher.publish(pin)
                count += 1
            except Exception:
                pin.status = PinStatus.FAILED
        return count

    def process_scheduled(self) -> int:
        """Publish all due scheduled pins."""
        pins = self.registry.get_all()
        due = self.scheduler.get_due_pins(pins)
        count = 0
        for pin in due:
            try:
                self.publisher.publish(pin)
                count += 1
            except Exception:
                pin.status = PinStatus.FAILED
        return count

    # ─── Analytics ────────────────────────────────────────

    def track_performance(self, pin_id: str, impressions: int = 0,
                           saves: int = 0, clicks: int = 0) -> PinAnalytics:
        return self.analytics.record(pin_id, impressions, saves, clicks)

    def simulate_daily(self, pin_id: str) -> Dict[str, Any]:
        pin = self.registry.get(pin_id)
        if not pin:
            return {}
        result = self.analytics.simulate_daily(pin)
        return result.to_dict()

    def get_top_pins(self, account_id: str = "", top_k: int = 5) -> List[PinterestPin]:
        pins = self.registry.get_by_account(account_id) if account_id else self.registry.get_all(status=PinStatus.PUBLISHED)
        return self.analytics.get_top_pins(pins, top_k)

    # ─── Health & Optimization ────────────────────────────

    def check_pin_health(self, pin_id: str) -> Dict[str, Any]:
        pin = self.registry.get(pin_id)
        if not pin:
            return {"error": "Pin not found"}
        all_pins = self.registry.get_all()
        return self.health.check_pin(pin, all_pins)

    def check_all_health(self, account_id: str = "") -> Dict[str, Any]:
        pins = self.registry.get_by_account(account_id) if account_id else self.registry.get_all()
        return self.health.check_all(pins)

    def analyze_pin(self, pin_id: str) -> Dict[str, Any]:
        pin = self.registry.get(pin_id)
        if not pin:
            return {"error": "Pin not found"}
        return self.optimizer.analyze_pin(pin, pin.ctr)

    # ─── Status ───────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        registry_stats = self.registry.get_stats()
        health_report = self.check_all_health()

        return {
            "module": "Pinterest Pin Manager (Layer 23 / Module 4)",
            "version": "1.0.0",
            "overall": "Healthy" if health_report["overall_score"] >= 70 else "Degraded",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "pins": registry_stats,
            "health": {
                "score": health_report["overall_score"],
                "healthy": health_report["healthy"],
                "degraded": health_report["degraded"],
                "critical": health_report["critical"],
                "issues": health_report["total_issues"],
            },
            "scheduler": self.scheduler.get_stats(),
            "publisher": self.publisher.get_stats(),
            "queue": self.queue.get_stats(),
            "analytics": self.analytics.get_stats(),
            "seo": self.seo.get_stats(),
            "optimizer": self.optimizer.get_stats(),
            "operations": {"total": self._total_operations},
        }

    def _log(self, operation: str, details: dict) -> None:
        with self._lock:
            self._total_operations += 1


# ─── Singleton ───────────────────────────────────────────────────────────────

_pin_manager_instance: Optional[PinterestPinManager] = None
_instance_lock = threading.Lock()


def get_pin_manager() -> PinterestPinManager:
    global _pin_manager_instance
    if _pin_manager_instance is None:
        with _instance_lock:
            if _pin_manager_instance is None:
                _pin_manager_instance = PinterestPinManager()
    return _pin_manager_instance
