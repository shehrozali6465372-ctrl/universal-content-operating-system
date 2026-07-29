"""ContentMappingEngine — Layer 23 / Module 5: AI Decision Brain for Pinterest Ecosystem.

Full pipeline: Article → Classification → Website → Account → Board → Pin Strategy
              → Affiliate → SEO → Image → Schedule → Validate → Recommend
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import (
    ContentMapping, ContentIntent, ContentAudience, PinStrategy, MappingPriority, MappingStatus,
)
from layers.layer23_website_manager.content_mapping_engine.models.mapping_history import MappingHistory
from layers.layer23_website_manager.content_mapping_engine.classifier.content_classifier import ContentClassifier
from layers.layer23_website_manager.content_mapping_engine.website_mapping.website_mapper import WebsiteMapper
from layers.layer23_website_manager.content_mapping_engine.account_mapping.account_mapper import PinterestAccountMapper
from layers.layer23_website_manager.content_mapping_engine.board_mapping.board_mapper import BoardMapper
from layers.layer23_website_manager.content_mapping_engine.board_mapping.pin_strategy import PinStrategyEngine
from layers.layer23_website_manager.content_mapping_engine.affiliate_mapping.affiliate_mapper import AffiliateMapper
from layers.layer23_website_manager.content_mapping_engine.seo_mapping.seo_mapper import SEOMapper
from layers.layer23_website_manager.content_mapping_engine.image_mapping.image_mapper import ImageMapper
from layers.layer23_website_manager.content_mapping_engine.scheduling.scheduling_mapper import SchedulingMapper
from layers.layer23_website_manager.content_mapping_engine.validation.validation_engine import ValidationEngine
from layers.layer23_website_manager.content_mapping_engine.relationships.relationship_engine import RelationshipEngine
from layers.layer23_website_manager.content_mapping_engine.recommendation.recommendation_engine import RecommendationEngine
from layers.layer23_website_manager.content_mapping_engine.exceptions import (
    ContentClassificationError, WebsiteMappingError, AccountMappingError,
    BoardMappingError, AffiliateMappingError,
)


class ContentMappingEngine:
    """Primary facade — AI decision engine for the entire Pinterest ecosystem.

    Full pipeline:
    Article → Classification → Website → Account → Board → Pin Strategy
    → Affiliate → SEO → Image → Schedule → Validate → Recommend
    Coordinates 12 sub-modules for intelligent content mapping.
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

        # Internal registry
        self._mappings: Dict[str, ContentMapping] = {}
        self._history: List[MappingHistory] = []
        self._total_operations = 0

    # ─── Core Pipeline ──────────────────────────────────────

    def map_article(self, title: str, content: str = "",
                     article_id: str = "",
                     keywords: Optional[List[str]] = None) -> ContentMapping:
        """Full pipeline: Article → Complete Mapping."""
        keywords = keywords or []

        # Step 1: Classify content
        classification = self.classifier.classify(title, content, keywords)
        niche = classification["niche"]

        # Step 2: Map to website
        website = self.website_mapper.map_to_website(niche, classification["category"], classification["topic"])

        # Step 3: Map to Pinterest account
        account = self.account_mapper.map_account(niche, classification["topic"])

        # Step 4: Map to board
        board = self.board_mapper.map_board(
            account["account_id"], classification["category"], keywords, classification["topic"]
        )

        # Step 5: Select pin strategy
        strategy = self.pin_strategy.select_strategy(
            classification["content_type"],
            ContentIntent(classification["intent"]),
            niche, keywords,
        )

        # Step 6: Map affiliate product
        try:
            affiliate = self.affiliate_mapper.map_affiliate(niche, keywords, classification["topic"])
        except AffiliateMappingError:
            affiliate = {"product_id": "", "product_name": "", "price": "",
                         "commission": 0.0, "affiliate_url": "", "confidence": 0.0}

        # Step 7: Generate SEO profile
        seo = self.seo_mapper.generate_seo_profile(title, niche, content, keywords)

        # Step 8: Map images
        images = self.image_mapper.map_images(niche, classification["content_type"], title)

        # Step 9: Determine schedule
        schedule = self.scheduling_mapper.map_schedule(
            niche, classification["intent"], classification["content_type"],
            classification["confidence"],
        )

        # Step 10: Build relationships
        relationships = self.relationship_engine.build_relationships(
            classification["topic"], niche, keywords,
        )

        # Build mapping object
        mapping = ContentMapping(
            article_id=article_id,
            article_title=title,
            niche=niche,
            category=classification["category"],
            subcategory=classification["subcategory"],
            topic=classification["topic"],
            intent=ContentIntent(classification["intent"]),
            audience=ContentAudience(classification["audience"]),
            content_type=classification["content_type"],
            confidence=classification["confidence"],
            website_id=website["website_id"],
            website_url=website["website_url"],
            website_category=website["website_category"],
            account_id=account["account_id"],
            account_name=account["account_name"],
            board_id=board["board_id"],
            board_name=board["board_name"],
            pin_strategy=PinStrategy(strategy["selected_strategy"]),
            affiliate_product_id=affiliate["product_id"],
            affiliate_product_name=affiliate["product_name"],
            affiliate_url=affiliate["affiliate_url"],
            affiliate_commission=affiliate.get("commission", 0.0),
            seo_keywords=seo["seo_keywords"],
            long_tail_keywords=seo["long_tail_keywords"],
            search_intent=seo["search_intent"],
            related_topics=seo["related_topics"],
            featured_image=images["featured_image"],
            pinterest_image=images["pinterest_image"],
            thumbnail=images["thumbnail"],
            image_style=images["image_style"],
            priority=MappingPriority(schedule["priority"]),
            schedule_time=schedule["schedule_time"],
            schedule_reason=schedule["schedule_reason"],
            related_article_ids=relationships["related_article_ids"],
            related_pin_ids=relationships["related_pin_ids"],
            related_board_ids=relationships["related_board_ids"],
            status=MappingStatus.ACTIVE,
        )

        # Step 11: Validate
        mapping_dict = mapping.to_dict()
        validation = self.validator.validate_mapping(mapping_dict)
        mapping.validation_score = validation["validation_score"]
        mapping.is_validated = validation["is_valid"]

        # Store mapping
        with self._lock:
            self._mappings[mapping.mapping_id] = mapping
            self._total_operations += 1

        return mapping

    def get_recommendations(self, mapping_id: str) -> Dict[str, Any]:
        """Get smart recommendations for a specific mapping."""
        mapping = self._mappings.get(mapping_id)
        if not mapping:
            return {"error": "Mapping not found"}
        return self.recommendation_engine.recommend(mapping.to_dict())

    # ─── CRUD ───────────────────────────────────────────────

    def get_mapping(self, mapping_id: str) -> Optional[ContentMapping]:
        return self._mappings.get(mapping_id)

    def get_all_mappings(self, status: Optional[MappingStatus] = None) -> List[ContentMapping]:
        if status:
            return [m for m in self._mappings.values() if m.status == status]
        return list(self._mappings.values())

    def get_mappings_by_niche(self, niche: str) -> List[ContentMapping]:
        return [m for m in self._mappings.values() if m.niche == niche]

    def get_mappings_by_account(self, account_id: str) -> List[ContentMapping]:
        return [m for m in self._mappings.values() if m.account_id == account_id]

    def get_mappings_by_website(self, website_id: str) -> List[ContentMapping]:
        return [m for m in self._mappings.values() if m.website_id == website_id]

    def update_mapping_status(self, mapping_id: str, status: MappingStatus) -> bool:
        mapping = self._mappings.get(mapping_id)
        if not mapping:
            return False
        with self._lock:
            old = mapping.to_dict()
            mapping.status = status
            mapping.updated_at = time.time()
            # Record history
            self._history.append(MappingHistory.create_change(
                mapping_id, old, mapping.to_dict(),
                f"Status changed to {status.value}"
            ))
        return True

    # ─── Stats ──────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics across all sub-modules."""
        by_status: Dict[str, int] = {}
        by_niche: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}

        for m in self._mappings.values():
            by_status[m.status.value] = by_status.get(m.status.value, 0) + 1
            by_niche[m.niche] = by_niche.get(m.niche, 0) + 1
            by_priority[m.priority.value] = by_priority.get(m.priority.value, 0) + 1

        validated_count = sum(1 for m in self._mappings.values() if m.is_validated)
        avg_confidence = sum(m.confidence for m in self._mappings.values()) / max(len(self._mappings), 1)
        avg_validation = sum(m.validation_score for m in self._mappings.values()) / max(len(self._mappings), 1)

        return {
            "module": "Content Mapping Engine (Layer 23 / Module 5)",
            "version": "1.0.0",
            "overall": "Healthy",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "total_mappings": len(self._mappings),
            "by_status": by_status,
            "by_niche": by_niche,
            "by_priority": by_priority,
            "validated": validated_count,
            "avg_confidence": round(avg_confidence, 2),
            "avg_validation_score": round(avg_validation, 1),
            "history_entries": len(self._history),
            "operations": self._total_operations,
            "classifier": self.classifier.get_stats(),
            "website_mapper": self.website_mapper.get_stats(),
            "account_mapper": self.account_mapper.get_stats(),
            "board_mapper": self.board_mapper.get_stats(),
            "pin_strategy": self.pin_strategy.get_stats(),
            "affiliate_mapper": self.affiliate_mapper.get_stats(),
            "seo_mapper": self.seo_mapper.get_stats(),
            "image_mapper": self.image_mapper.get_stats(),
            "scheduling": self.scheduling_mapper.get_stats(),
            "validator": self.validator.get_stats(),
            "relationships": self.relationship_engine.get_stats(),
            "recommendations": self.recommendation_engine.get_stats(),
        }

    def get_status(self) -> Dict[str, Any]:
        """Alias for get_stats."""
        return self.get_stats()

    def _log(self, operation: str) -> None:
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
