"""ContentMappingEngine — Layer 23 / Module 5.

AI Decision Engine that maps content to the correct website, Pinterest account,
board, pin strategy, affiliate product, SEO profile, and publishing schedule.

Flow: Article → Classify → Website → Account → Board → Strategy → Affiliate → SEO → Schedule → Validate
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import (
    ContentMapping, ContentMapping, MappingStatus, PinStrategy, Priority,
    ContentCategory, ContentIntent,
)
from layers.layer23_website_manager.content_mapping_engine.models.mapping_history import MappingHistory
from layers.layer23_website_manager.content_mapping_engine.classifier.content_classifier import ContentClassifier
from layers.layer23_website_manager.content_mapping_engine.website_mapping.website_mapper import WebsiteMapper
from layers.layer23_website_manager.content_mapping_engine.account_mapping.pinterest_account_mapper import PinterestAccountMapper
from layers.layer23_website_manager.content_mapping_engine.board_mapping.board_mapper import BoardMapper
from layers.layer23_website_manager.content_mapping_engine.board_mapping.pin_strategy_engine import PinStrategyEngine
from layers.layer23_website_manager.content_mapping_engine.affiliate_mapping.affiliate_mapper import AffiliateMapper
from layers.layer23_website_manager.content_mapping_engine.seo_mapping.seo_mapper import SEOMapper
from layers.layer23_website_manager.content_mapping_engine.image_mapping.image_mapper import ImageMapper
from layers.layer23_website_manager.content_mapping_engine.scheduling.scheduling_mapper import SchedulingMapper
from layers.layer23_website_manager.content_mapping_engine.validation.validation_engine import ValidationEngine
from layers.layer23_website_manager.content_mapping_engine.relationships.relationship_engine import RelationshipEngine
from layers.layer23_website_manager.content_mapping_engine.recommendation.recommendation_engine import RecommendationEngine
from layers.layer23_website_manager.content_mapping_engine.exceptions import (
    ContentClassificationError, WebsiteMappingError, AccountMappingError,
    BoardMappingError, AffiliateMappingError, ValidationError,
)


class ContentMappingEngine:
    """Primary facade for Content Mapping Engine.

    Full pipeline: Article → Classify → Website → Account → Board → Strategy
                   → Affiliate → SEO → Image → Schedule → Validate → Recommend
    Coordinates 12 sub-modules for end-to-end AI decision making.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()

        # Sub-modules
        self.classifier = ContentClassifier()
        self.website_mapper = WebsiteMapper()
        self.account_mapper = PinterestAccountMapper()
        self.board_mapper = BoardMapper()
        self.pin_strategy = PinStrategyEngine()
        self.affiliate_mapper = AffiliateMapper()
        self.seo_mapper = SEOMapper()
        self.image_mapper = ImageMapper()
        self.scheduling_mapper = SchedulingMapper()
        self.validator = ValidationEngine()
        self.relationship_engine = RelationshipEngine()
        self.recommendation_engine = RecommendationEngine()

        # Storage
        self._mappings: Dict[str, ContentMapping] = {}
        self._history: List[MappingHistory] = []
        self._total_operations = 0

    # ─── Full Pipeline ────────────────────────────────────

    def map_content(self, article_title: str, article_content: str = "",
                     article_id: str = "", keywords: Optional[List[str]] = None,
                     preferred_website: str = "", preferred_account: str = "",
                     preferred_board: str = "") -> ContentMapping:
        """Full mapping pipeline: Classify → Website → Account → Board → Strategy → Affiliate → SEO → Schedule."""
        mapping = ContentMapping(
            article_id=article_id,
            article_title=article_title,
            article_content=article_content[:1000],
        )

        # Step 1: Classify content
        classification = self.classifier.classify(article_title, article_content, keywords or [])
        mapping.niche = classification["niche"]
        mapping.category = ContentCategory(classification["category"])
        mapping.intent = ContentIntent(classification["intent"])
        mapping.audience = classification["audience"]
        mapping.content_type = classification["content_type"]
        mapping.confidence = classification["confidence"]

        # Step 2: Map website
        ws = self.website_mapper.map_website(mapping.niche, classification["category"],
                                              preferred_website)
        mapping.website_id = ws.get("id", "")
        mapping.website_url = f"https://{ws.get('domain', '')}" if ws.get("domain") else ""

        # Step 3: Map Pinterest account
        acc = self.account_mapper.map_account(mapping.niche, preferred_account)
        mapping.account_id = acc.get("id", "")
        mapping.account_name = acc.get("name", "")

        # Step 4: Map board
        brd = self.board_mapper.map_board(mapping.niche, article_title, preferred_board)
        mapping.board_id = brd.get("id", "")
        mapping.board_name = brd.get("name", "")

        # Step 5: Select pin strategy
        strategy = self.pin_strategy.select_strategy(
            mapping.niche, mapping.intent.value, mapping.content_type,
            has_multiple_images=False,
        )
        mapping.pin_strategy = PinStrategy(strategy["strategy"])
        mapping.pin_type_reason = strategy["reason"]

        # Step 6: Map affiliate
        aff = self.affiliate_mapper.map_affiliate(mapping.niche, article_title)
        mapping.affiliate_product = aff.get("product", "")
        mapping.affiliate_url = aff.get("url", "")
        mapping.affiliate_program = aff.get("program", "")
        mapping.affiliate_commission = aff.get("commission", 0.0)

        # Step 7: SEO profile
        seo = self.seo_mapper.generate_seo_profile(mapping.niche, mapping.intent.value, article_title)
        mapping.seo_keywords = seo["keywords"]
        mapping.long_tail_keywords = seo["long_tail_keywords"]
        mapping.search_intent = seo["search_intent"]
        mapping.related_topics = seo["related_topics"]

        # Step 8: Image mapping
        img = self.image_mapper.map_images(mapping.niche, mapping.content_type)
        mapping.featured_image = img["featured_image_style"]
        mapping.pin_image = img["pin_image_orientation"]
        mapping.image_style = img["image_vibe"]

        # Step 9: Scheduling
        existing_queue = len([m for m in self._mappings.values() if m.status == MappingStatus.PENDING])
        sched = self.scheduling_mapper.schedule(mapping.niche, mapping.intent.value,
                                                  mapping.confidence, existing_queue)
        mapping.priority = Priority(sched["priority"])
        mapping.suggested_publish_time = sched["suggested_publish_time"]
        mapping.schedule_reason = sched["schedule_reason"]

        # Step 10: Validate
        mapping.status = MappingStatus.MAPPED
        self.validator.validate_mapping(mapping)

        # Store mapping
        self._mappings[mapping.mapping_id] = mapping
        self._log("map_content", {"article": article_title})

        return mapping

    # ─── Individual Mapping Steps ─────────────────────────

    def classify(self, title: str, content: str = "",
                  keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.classifier.classify(title, content, keywords or [])

    def map_website(self, niche: str, category: str = "",
                     preferred: str = "") -> Dict[str, Any]:
        return self.website_mapper.map_website(niche, category, preferred)

    def map_account(self, niche: str, preferred: str = "") -> Dict[str, Any]:
        return self.account_mapper.map_account(niche, preferred)

    def map_board(self, niche: str, topic: str = "",
                   preferred: str = "") -> Dict[str, Any]:
        return self.board_mapper.map_board(niche, topic, preferred)

    def select_strategy(self, niche: str, intent: str, content_type: str) -> Dict[str, Any]:
        return self.pin_strategy.select_strategy(niche, intent, content_type)

    def map_affiliate(self, niche: str, topic: str = "") -> Dict[str, Any]:
        return self.affiliate_mapper.map_affiliate(niche, topic)

    def generate_seo(self, niche: str, intent: str, title: str = "") -> Dict[str, Any]:
        return self.seo_mapper.generate_seo_profile(niche, intent, title)

    def map_images(self, niche: str, content_type: str = "article") -> Dict[str, Any]:
        return self.image_mapper.map_images(niche, content_type)

    def schedule(self, niche: str, intent: str, confidence: float) -> Dict[str, Any]:
        return self.scheduling_mapper.schedule(niche, intent, confidence)

    # ─── Validation & Recommendations ─────────────────────

    def validate(self, mapping_id: str) -> Dict[str, Any]:
        mapping = self._mappings.get(mapping_id)
        if not mapping:
            return {"error": "Mapping not found"}
        return self.validator.validate_mapping(mapping)

    def recommend(self, mapping_id: str) -> Dict[str, Any]:
        mapping = self._mappings.get(mapping_id)
        if not mapping:
            return {"error": "Mapping not found"}
        self._log("recommend", {"mapping_id": mapping_id})
        return self.recommendation_engine.recommend_improvements(mapping)

    def build_relationships(self, mapping_id: str) -> Dict[str, Any]:
        mapping = self._mappings.get(mapping_id)
        if not mapping:
            return {"error": "Mapping not found"}
        return self.relationship_engine.build_relationships(mapping.niche, mapping.article_title)

    # ─── Mapping Management ───────────────────────────────

    def get_mapping(self, mapping_id: str) -> Optional[ContentMapping]:
        return self._mappings.get(mapping_id)

    def get_mappings_by_niche(self, niche: str) -> List[ContentMapping]:
        return [m for m in self._mappings.values() if m.niche == niche]

    def get_mappings_by_account(self, account_id: str) -> List[ContentMapping]:
        return [m for m in self._mappings.values() if m.account_id == account_id]

    def get_all_mappings(self, status: Optional[MappingStatus] = None) -> List[ContentMapping]:
        mappings = list(self._mappings.values())
        if status:
            mappings = [m for m in mappings if m.status == status]
        return sorted(mappings, key=lambda m: m.created_at, reverse=True)

    def delete_mapping(self, mapping_id: str) -> bool:
        return self._mappings.pop(mapping_id, None) is not None

    # ─── Status ───────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        by_niche: Dict[str, int] = {}
        for m in self._mappings.values():
            by_niche[m.niche] = by_niche.get(m.niche, 0) + 1

        validated = sum(1 for m in self._mappings.values() if m.is_validated)
        pending = sum(1 for m in self._mappings.values() if m.status == MappingStatus.PENDING)

        return {
            "module": "Content Mapping Engine (Layer 23 / Module 5)",
            "version": "1.0.0",
            "overall": "Healthy" if len(self._mappings) > 0 else "Idle",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "mappings": {
                "total": len(self._mappings),
                "validated": validated,
                "pending": pending,
                "by_niche": by_niche,
            },
            "classifier": self.classifier.get_stats(),
            "website_mapper": self.website_mapper.get_stats(),
            "account_mapper": self.account_mapper.get_stats(),
            "board_mapper": self.board_mapper.get_stats(),
            "pin_strategy": self.pin_strategy.get_stats(),
            "affiliate_mapper": self.affiliate_mapper.get_stats(),
            "seo_mapper": self.seo_mapper.get_stats(),
            "image_mapper": self.image_mapper.get_stats(),
            "scheduling_mapper": self.scheduling_mapper.get_stats(),
            "validator": self.validator.get_stats(),
            "relationship_engine": self.relationship_engine.get_stats(),
            "recommendation_engine": self.recommendation_engine.get_stats(),
            "operations": {"total": self._total_operations},
        }

    def _log(self, operation: str, details: dict) -> None:
        with self._lock:
            self._total_operations += 1


# ─── Singleton ───────────────────────────────────────────────────────────────

_mapping_engine_instance: Optional[ContentMappingEngine] = None
_instance_lock = threading.Lock()


def get_mapping_engine() -> ContentMappingEngine:
    global _mapping_engine_instance
    if _mapping_engine_instance is None:
        with _instance_lock:
            if _mapping_engine_instance is None:
                _mapping_engine_instance = ContentMappingEngine()
    return _mapping_engine_instance
