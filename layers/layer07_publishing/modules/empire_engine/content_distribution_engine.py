"""ContentDistributionEngine — One content → multiple platform formats."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class ContentPiece:
    __slots__ = ("id", "title", "original_content", "content_type", "niche",
                 "language", "tags", "created_at")

    def __init__(self, title: str, original_content: str, content_type: str = "article",
                 niche: str = "", language: str = "en") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.title = title
        self.original_content = original_content
        self.content_type = content_type
        self.niche = niche
        self.language = language
        self.tags: List[str] = []
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "title": self.title,
            "type": self.content_type, "niche": self.niche,
            "language": self.language, "tags": self.tags,
        }


class AdaptedContent:
    __slots__ = ("id", "original_id", "platform", "format", "title",
                 "content", "hashtags", "mentions", "cta", "char_count",
                 "image_required", "video_required", "scheduled")

    def __init__(self, original_id: str, platform: str, format_type: str = "post") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.original_id = original_id
        self.platform = platform
        self.format = format_type
        self.title = ""
        self.content = ""
        self.hashtags: List[str] = []
        self.mentions: List[str] = []
        self.cta = ""
        self.char_count = 0
        self.image_required = False
        self.video_required = False
        self.scheduled = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "original_id": self.original_id,
            "platform": self.platform, "format": self.format,
            "title": self.title, "char_count": self.char_count,
            "hashtags": self.hashtags, "cta": self.cta,
            "image_required": self.image_required,
        }


PLATFORM_FORMATS = {
    "facebook": {"max_chars": 63206, "format": "post", "image": True, "hashtag_limit": 5},
    "instagram": {"max_chars": 2200, "format": "caption", "image": True, "hashtag_limit": 30},
    "x": {"max_chars": 280, "format": "tweet", "image": True, "hashtag_limit": 3},
    "linkedin": {"max_chars": 3000, "format": "post", "image": True, "hashtag_limit": 5},
    "tiktok": {"max_chars": 2200, "format": "caption", "video": True, "hashtag_limit": 5},
    "youtube": {"max_chars": 5000, "format": "description", "video": True, "hashtag_limit": 15},
    "pinterest": {"max_chars": 500, "format": "pin", "image": True, "hashtag_limit": 20},
    "wordpress": {"max_chars": 100000, "format": "blog_post", "hashtag_limit": 0},
    "medium": {"max_chars": 100000, "format": "article", "hashtag_limit": 0},
    "twitter_thread": {"max_chars": 280, "format": "thread", "image": True, "hashtag_limit": 3},
}


class ContentDistributionEngine:
    """Adapts one piece of content into multiple platform-specific formats."""
    _instance: Optional["ContentDistributionEngine"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ContentDistributionEngine":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._content_pieces: Dict[str, ContentPiece] = {}
        self._adapted: Dict[str, List[AdaptedContent]] = {}
        self._distribution_log: List[Dict[str, Any]] = []

    def create_content(self, title: str, content: str, content_type: str = "article",
                       niche: str = "", language: str = "en",
                       tags: List[str] = None) -> ContentPiece:
        piece = ContentPiece(title, content, content_type, niche, language)
        if tags:
            piece.tags = tags
        self._content_pieces[piece.id] = piece
        return piece

    def adapt_for_platform(self, content_id: str, platform: str) -> Optional[AdaptedContent]:
        piece = self._content_pieces.get(content_id)
        if not piece:
            return None
        fmt = PLATFORM_FORMATS.get(platform, PLATFORM_FORMATS["facebook"])
        adapted = AdaptedContent(content_id, platform, fmt["format"])
        max_chars = fmt["max_chars"]
        if platform in ("x", "twitter_thread"):
            adapted.title = piece.title[:280]
            adapted.content = piece.original_content[:max_chars]
        elif platform in ("wordpress", "medium"):
            adapted.title = piece.title
            adapted.content = piece.original_content
        elif platform == "instagram":
            adapted.title = piece.title[:150]
            adapted.content = piece.original_content[:max_chars]
        else:
            adapted.title = piece.title[:200]
            adapted.content = piece.original_content[:max_chars]
        adapted.char_count = len(adapted.content)
        adapted.image_required = fmt.get("image", False)
        adapted.video_required = fmt.get("video", False)
        adapted.hashtags = self._generate_hashtags(piece, fmt.get("hashtag_limit", 5))
        self._adapted.setdefault(content_id, []).append(adapted)
        return adapted

    def distribute(self, content_id: str, platforms: List[str]) -> List[AdaptedContent]:
        results = []
        for platform in platforms:
            adapted = self.adapt_for_platform(content_id, platform)
            if adapted:
                results.append(adapted)
        self._distribution_log.append({
            "content_id": content_id,
            "platforms": platforms,
            "adapted_count": len(results),
            "timestamp": time.time(),
        })
        return results

    def _generate_hashtags(self, piece: ContentPiece, limit: int) -> List[str]:
        hashtags = []
        if piece.niche:
            hashtags.append(f"#{piece.niche.replace(' ', '')}")
        for tag in piece.tags[:limit - 1]:
            hashtags.append(f"#{tag.replace(' ', '')}")
        return hashtags[:limit]

    def get_content(self, content_id: str) -> Optional[ContentPiece]:
        return self._content_pieces.get(content_id)

    def get_adapted(self, content_id: str) -> List[AdaptedContent]:
        return self._adapted.get(content_id, [])

    def get_all_content(self) -> List[ContentPiece]:
        return list(self._content_pieces.values())

    def get_distribution_status(self) -> Dict[str, Any]:
        all_adapted = []
        for adapted_list in self._adapted.values():
            all_adapted.extend(adapted_list)
        platforms_used = set(a.platform for a in all_adapted)
        return {
            "total_content": len(self._content_pieces),
            "total_adapted": len(all_adapted),
            "platforms_used": list(platforms_used),
            "distributions": len(self._distribution_log),
            "avg_adaptations_per_content": round(
                len(all_adapted) / len(self._content_pieces), 1
            ) if self._content_pieces else 0,
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "content_pieces": len(self._content_pieces),
            "adapted_content": sum(len(a) for a in self._adapted.values()),
            "distributions": len(self._distribution_log),
        }


def get_content_distribution() -> ContentDistributionEngine:
    return ContentDistributionEngine()
