"""Writing Memory — Brand voice consistency across all platforms."""
from __future__ import annotations
import time
from threading import RLock
from uuid import uuid4
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
    __slots__ = ("record_id", "account_id", "platform", "topic", "text", "tone",
                 "brand_voice", "tokens_used", "created_at")

    def __init__(self, platform: str = "", topic: str = "", text: str = "", account_id: str = "default") -> None:
        self.record_id = f"wm_{uuid4().hex}"
        self.account_id = account_id
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
            "account_id": self.account_id,
            "platform": self.platform,
            "topic": self.topic,
            "text_preview": self.text[:80] + "..." if len(self.text) > 80 else self.text,
        }


class WritingMemory:
    """Stores brand voice and past content for consistency."""

    def __init__(self, max_size: int = 500) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._voices: Dict[str, BrandVoice] = {}
        self._records: List[DraftRecord] = []
        self._max_size = max_size
        self._platform_index: Dict[str, List[int]] = {}
        self._lock = RLock()

    def set_voice(self, name: str, tone: str = "friendly",
                  personality: Optional[List[str]] = None,
                  dos: Optional[List[str]] = None,
                  donts: Optional[List[str]] = None) -> BrandVoice:
        """Set or update brand voice."""
        voice = BrandVoice(name=name)
        voice.tone = tone
        voice.personality = list(personality or [])
        voice.dos = list(dos or [])
        voice.donts = list(donts or [])
        with self._lock:
            self._voices[name] = voice
            return self._copy_voice(voice)

    def get_voice(self, name: str) -> Optional[BrandVoice]:
        with self._lock:
            voice = self._voices.get(name)
            return self._copy_voice(voice) if voice else None

    def store_draft(self, platform: str, topic: str, text: str,
                    tone: str = "", brand_voice: str = "",
                    tokens: int = 0, account_id: str = "default") -> DraftRecord:
        """Store a generated draft."""
        rec = DraftRecord(platform=platform, topic=topic, text=text, account_id=account_id)
        rec.tone = tone
        rec.brand_voice = brand_voice
        if tokens < 0:
            raise ValueError("tokens must be non-negative")
        rec.tokens_used = tokens
        with self._lock:
            if len(self._records) >= self._max_size:
                self._records.pop(0)
            self._rebuild_index_locked()
            self._records.append(rec)
            self._rebuild_index_locked()
        return rec

    def get_by_platform(self, platform: str, limit: int = 10) -> List[DraftRecord]:
        if limit < 1:
            return []
        with self._lock:
            idxs = self._platform_index.get(platform, [])
            return [self._copy_record(self._records[i]) for i in idxs if i < len(self._records)][:limit]

    def get_history(self, account_id: str = "default", platform: Optional[str] = None, limit: int = 50) -> List[DraftRecord]:
        if limit < 1:
            return []
        with self._lock:
            records = [r for r in self._records if r.account_id == account_id and
                   (platform is None or r.platform == platform)]
            return [self._copy_record(r) for r in records[-limit:]]

    def get_recent(self, limit: int = 10) -> List[DraftRecord]:
        if limit < 1:
            return []
        with self._lock:
            return [self._copy_record(r) for r in self._records[-limit:]]

    def check_consistency(self, text: str, voice_name: str) -> Dict[str, Any]:
        """Check if text matches brand voice."""
        with self._lock:
            voice = self._voices.get(voice_name)
            voice = self._copy_voice(voice) if voice else None
        if not voice:
            return {"consistent": True, "reason": "No voice profile found"}
        issues: List[str] = []
        for dont in voice.donts:
            if dont.lower() in text.lower():
                issues.append(f"Contains prohibited: '{dont}'")
        return {"consistent": len(issues) == 0, "issues": issues}

    @staticmethod
    def _copy_record(record: DraftRecord) -> DraftRecord:
        copy = DraftRecord(record.platform, record.topic, record.text, record.account_id)
        copy.record_id = record.record_id
        copy.tone = record.tone
        copy.brand_voice = record.brand_voice
        copy.tokens_used = record.tokens_used
        copy.created_at = record.created_at
        return copy

    @staticmethod
    def _copy_voice(voice: BrandVoice) -> BrandVoice:
        copy = BrandVoice(voice.name)
        copy.tone = voice.tone
        copy.vocabulary_level = voice.vocabulary_level
        copy.personality = list(voice.personality)
        copy.dos = list(voice.dos)
        copy.donts = list(voice.donts)
        copy.platform_profiles = {k: dict(v) for k, v in voice.platform_profiles.items()}
        copy.created_at = voice.created_at
        return copy

    def _rebuild_index_locked(self) -> None:
        self._platform_index = {}
        for idx, record in enumerate(self._records):
            self._platform_index.setdefault(record.platform, []).append(idx)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._records)

    @property
    def voice_count(self) -> int:
        with self._lock:
            return len(self._voices)
