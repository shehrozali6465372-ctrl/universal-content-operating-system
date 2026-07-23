"""KeywordIntelligence — Buyer intent, commercial, long-tail, question keywords."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class KeywordEntry:
    __slots__ = ("id", "keyword", "niche", "intent_type", "search_volume",
                 "difficulty", "cpc", "competition", "trend", "long_tail",
                 "word_count", "question", "commercial_score", "content_type",
                 "last_analyzed")

    INTENT_TYPES = ("informational", "navigational", "commercial", "transactional")

    def __init__(self, keyword: str, niche: str = "", intent_type: str = "informational") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.keyword = keyword
        self.niche = niche
        self.intent_type = intent_type
        self.search_volume = 0
        self.difficulty = 50.0
        self.cpc = 0.0
        self.competition = "medium"
        self.trend = "stable"
        self.long_tail = len(keyword.split()) > 3
        self.word_count = len(keyword.split())
        self.question = any(keyword.lower().startswith(q) for q in
                           ("how", "what", "why", "when", "where", "which", "who", "is", "can"))
        self.commercial_score = 0.0
        self.content_type = "blog"
        self.last_analyzed = time.time()

    @property
    def opportunity_score(self) -> float:
        vol_score = min(self.search_volume / 10000, 1.0) * 25
        diff_score = max(1 - (self.difficulty / 100), 0) * 30
        cpc_score = min(self.cpc / 5, 1.0) * 25
        intent_bonus = {"transactional": 15, "commercial": 12, "informational": 5, "navigational": 2}.get(
            self.intent_type, 5
        )
        long_tail_bonus = 5 if self.long_tail else 0
        return vol_score + diff_score + cpc_score + intent_bonus + long_tail_bonus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "keyword": self.keyword, "niche": self.niche,
            "intent": self.intent_type, "volume": self.search_volume,
            "difficulty": round(self.difficulty, 1), "cpc": round(self.cpc, 2),
            "competition": self.competition, "trend": self.trend,
            "long_tail": self.long_tail, "question": self.question,
            "word_count": self.word_count, "content_type": self.content_type,
            "opportunity": round(self.opportunity_score, 1),
        }


class KeywordIntelligence:
    """Discovers, categorizes, and scores keywords for content strategy."""
    _instance: Optional["KeywordIntelligence"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "KeywordIntelligence":
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
        self._keywords: Dict[str, KeywordEntry] = {}
        self._niche_index: Dict[str, List[str]] = {}
        self._intent_index: Dict[str, List[str]] = {}

    def add_keyword(self, keyword: str, niche: str = "", intent_type: str = "informational",
                    volume: int = 0, difficulty: float = 50.0, cpc: float = 0.0,
                    competition: str = "medium", trend: str = "stable",
                    content_type: str = "blog") -> KeywordEntry:
        entry = KeywordEntry(keyword, niche, intent_type)
        entry.search_volume = volume
        entry.difficulty = difficulty
        entry.cpc = cpc
        entry.competition = competition
        entry.trend = trend
        entry.content_type = content_type
        self._keywords[entry.id] = entry
        if niche:
            self._niche_index.setdefault(niche, []).append(entry.id)
        self._intent_index.setdefault(intent_type, []).append(entry.id)
        return entry

    def get_keyword(self, kid: str) -> Optional[KeywordEntry]:
        return self._keywords.get(kid)

    def search(self, query: str) -> List[KeywordEntry]:
        q = query.lower()
        return [k for k in self._keywords.values() if q in k.keyword.lower()]

    def get_by_niche(self, niche: str) -> List[KeywordEntry]:
        ids = self._niche_index.get(niche, [])
        return [self._keywords[i] for i in ids if i in self._keywords]

    def get_by_intent(self, intent_type: str) -> List[KeywordEntry]:
        ids = self._intent_index.get(intent_type, [])
        return [self._keywords[i] for i in ids if i in self._keywords]

    def get_buyer_intent(self) -> List[KeywordEntry]:
        return sorted(
            [k for k in self._keywords.values() if k.intent_type in ("transactional", "commercial")],
            key=lambda k: k.opportunity_score, reverse=True,
        )

    def get_long_tail(self) -> List[KeywordEntry]:
        return sorted(
            [k for k in self._keywords.values() if k.long_tail],
            key=lambda k: k.opportunity_score, reverse=True,
        )

    def get_questions(self) -> List[KeywordEntry]:
        return sorted(
            [k for k in self._keywords.values() if k.question],
            key=lambda k: k.opportunity_score, reverse=True,
        )

    def get_commercial_keywords(self) -> List[KeywordEntry]:
        return sorted(
            [k for k in self._keywords.values() if k.intent_type == "commercial"],
            key=lambda k: k.cpc, reverse=True,
        )

    def get_top_keywords(self, metric: str = "opportunity", limit: int = 10) -> List[KeywordEntry]:
        kws = list(self._keywords.values())
        key_map = {
            "opportunity": lambda k: k.opportunity_score,
            "volume": lambda k: k.search_volume,
            "cpc": lambda k: k.cpc,
            "difficulty_low": lambda k: 100 - k.difficulty,
        }
        fn = key_map.get(metric, key_map["opportunity"])
        return sorted(kws, key=fn, reverse=True)[:limit]

    def get_keyword_report(self) -> Dict[str, Any]:
        kws = list(self._keywords.values())
        return {
            "total_keywords": len(kws),
            "by_intent": {i: len([k for k in kws if k.intent_type == i])
                         for i in KeywordEntry.INTENT_TYPES},
            "by_niche": {n: len(ids) for n, ids in self._niche_index.items()},
            "long_tail": sum(1 for k in kws if k.long_tail),
            "questions": sum(1 for k in kws if k.question),
            "avg_volume": round(
                sum(k.search_volume for k in kws) / len(kws), 0
            ) if kws else 0,
            "avg_cpc": round(
                sum(k.cpc for k in kws) / len(kws), 2
            ) if kws else 0,
            "top_10": [k.to_dict() for k in self.get_top_keywords(limit=10)],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "keywords": len(self._keywords),
            "niches": len(self._niche_index),
            "intents": len(self._intent_index),
        }


def get_keyword_intelligence() -> KeywordIntelligence:
    return KeywordIntelligence()
