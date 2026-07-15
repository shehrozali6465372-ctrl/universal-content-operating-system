"""Writing Memory — Brand voice consistency across all platforms."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class BrandVoice:
    """Brand voice profile."""
    __slots__ = ("name", "tone", "vocabulary_level", "personality", "dos", "donts",
                 "platform_profiles", "created_at")

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.tone = "friendly"
        self.vocabulary_level = "simple"
        self.personality: List[str] = []
        self.dos: List[str] = []
        self.donts: List[str] = []
        self.platform_profiles: Dict[str, Dict[str, Any]] = {}
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tone": self.tone,
            "vocabulary_level": self.vocabulary_level,
            "personality": self.personality,
            "dos": self.dos,
            "donts": self.donts,
            "platform_profiles": self.platform_profiles,
        }


class DraftRecord:
    """A stored draft with brand voice tracking."""
    __slots__ = ("record_id", "platform", "topic", "text", "tone",
                 "brand_voice", "tokens_used", "created_at")

    def __init__(self, platform: str = "", topic: str = "", text: str = "") -> None:
        self.record_id = f"wm_{int(time.time() * 1000) % 10000000}"
        self.platform = platform
        self.topic = topic
        self.text = text
        self.tone = ""
        self.brand_voice = ""
        self.tokens_used = 0
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "platform": self.platform,
            "topic": self.topic,
            "text_preview": self.text[:80] + "..." if len(self.text) > 80 else self.text,
        }


class WritingMemory:
    """Stores brand voice and past content for consistency."""

    def __init__(self, max_size: int = 500) -> None:
        self._voices: Dict[str, BrandVoice] = {}
        self._records: List[DraftRecord] = []
        self._max_size = max_size
        self._platform_index: Dict[str, List[int]] = {}

    def set_voice(self, name: str, tone: str = "friendly",
                  personality: Optional[List[str]] = None,
                  dos: Optional[List[str]] = None,
                  donts: Optional[List[str]] = None) -> BrandVoice:
        """Set or update brand voice."""
        voice = BrandVoice(name=name)
        voice.tone = tone
        voice.personality = personality or []
        voice.dos = dos or []
        voice.donts = donts or []
        self._voices[name] = voice
        return voice

    def get_voice(self, name: str) -> Optional[BrandVoice]:
        return self._voices.get(name)

    def store_draft(self, platform: str, topic: str, text: str,
                    tone: str = "", brand_voice: str = "",
                    tokens: int = 0) -> DraftRecord:
        """Store a generated draft."""
        rec = DraftRecord(platform=platform, topic=topic, text=text)
        rec.tone = tone
        rec.brand_voice = brand_voice
        rec.tokens_used = tokens
        if len(self._records) >= self._max_size:
            self._records.pop(0)
        idx = len(self._records)
        self._records.append(rec)
        self._platform_index.setdefault(platform, []).append(idx)
        return rec

    def get_by_platform(self, platform: str, limit: int = 10) -> List[DraftRecord]:
        idxs = self._platform_index.get(platform, [])
        return [self._records[i] for i in idxs if i < len(self._records)][:limit]

    def get_recent(self, limit: int = 10) -> List[DraftRecord]:
        return self._records[-limit:]

    def check_consistency(self, text: str, voice_name: str) -> Dict[str, Any]:
        """Check if text matches brand voice."""
        voice = self._voices.get(voice_name)
        if not voice:
            return {"consistent": True, "reason": "No voice profile found"}
        issues: List[str] = []
        for dont in voice.donts:
            if dont.lower() in text.lower():
                issues.append(f"Contains prohibited: '{dont}'")
        return {"consistent": len(issues) == 0, "issues": issues}

    @property
    def count(self) -> int:
        return len(self._records)

    @property
    def voice_count(self) -> int:
        return len(self._voices)
