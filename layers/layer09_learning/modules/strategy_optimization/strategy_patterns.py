"""Strategy Patterns — Detect patterns in strategy performance."""
from __future__ import annotations
import time
from typing import Any, Dict, List

from layers.layer09_learning.modules.strategy_optimization.strategy_profile import StrategyProfile


class StrategyPattern:
    """A detected pattern in strategy performance."""

    __slots__ = ("pattern_id", "pattern_type", "description", "confidence",
                 "frequency", "platform", "tags")

    PATTERN_TYPES = ("success", "failure", "seasonal", "platform_specific", "audience_shift")

    def __init__(self, pattern_type: str = "", description: str = "") -> None:
        self.pattern_id: str = f"sp_{int(time.time() * 1000) % 100000}"
        self.pattern_type = pattern_type if pattern_type in self.PATTERN_TYPES else "success"
        self.description = description
        self.confidence: float = 0.0
        self.frequency: int = 0
        self.platform: str = ""
        self.tags: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "frequency": self.frequency,
            "platform": self.platform,
        }


class StrategyPatternDetector:
    """Detect patterns in strategy performance across multiple strategies."""

    MIN_FREQUENCY = 2

    def __init__(self) -> None:
        self._patterns: List[StrategyPattern] = []
        self._detection_count: int = 0

    def detect(self, strategies: List[StrategyProfile]) -> List[StrategyPattern]:
        self._patterns.clear()
        if not strategies:
            return self._patterns
        self._detect_high_performers(strategies)
        self._detect_low_performers(strategies)
        self._detect_platform_patterns(strategies)
        self._detect_frequency_patterns(strategies)
        self._detection_count += 1
        return list(self._patterns)

    def _detect_high_performers(self, strategies: List[StrategyProfile]) -> None:
        high = [s for s in strategies if s.effective_score > 0.7 and s.usage_count >= self.MIN_FREQUENCY]
        if len(high) >= self.MIN_FREQUENCY:
            for platform in set(p for s in high for p in s.target_platforms):
                platform_strats = [s for s in high if platform in s.target_platforms]
                if len(platform_strats) >= self.MIN_FREQUENCY:
                    p = StrategyPattern("success", f"High-performing strategies on {platform}")
                    p.confidence = min(1.0, len(platform_strats) / max(1, len(strategies)))
                    p.frequency = len(platform_strats)
                    p.platform = platform
                    self._patterns.append(p)

    def _detect_low_performers(self, strategies: List[StrategyProfile]) -> None:
        low = [s for s in strategies if s.effective_score < 0.3 and s.usage_count >= self.MIN_FREQUENCY]
        if len(low) >= self.MIN_FREQUENCY:
            p = StrategyPattern("failure", f"{len(low)} strategies underperforming")
            p.confidence = min(1.0, len(low) / max(1, len(strategies)))
            p.frequency = len(low)
            self._patterns.append(p)

    def _detect_platform_patterns(self, strategies: List[StrategyProfile]) -> None:
        platform_scores: Dict[str, List[float]] = {}
        for s in strategies:
            for platform in s.target_platforms:
                platform_scores.setdefault(platform, []).append(s.effective_score)
        for platform, scores in platform_scores.items():
            if len(scores) >= self.MIN_FREQUENCY:
                avg = sum(scores) / len(scores)
                if avg > 0.6:
                    p = StrategyPattern("platform_specific", f"Platform {platform} averages {avg:.2f} effectiveness")
                    p.confidence = 0.8
                    p.frequency = len(scores)
                    p.platform = platform
                    self._patterns.append(p)

    def _detect_frequency_patterns(self, strategies: List[StrategyProfile]) -> None:
        freq_map: Dict[str, List[float]] = {}
        for s in strategies:
            freq_map.setdefault(s.posting_frequency, []).append(s.effective_score)
        for freq, scores in freq_map.items():
            if len(scores) >= self.MIN_FREQUENCY:
                avg = sum(scores) / len(scores)
                p = StrategyPattern("seasonal", f"Frequency '{freq}' avg score {avg:.2f}")
                p.confidence = 0.7
                p.frequency = len(scores)
                p.tags.append(freq)
                self._patterns.append(p)

    def get_patterns(self, pattern_type: str = "") -> List[StrategyPattern]:
        if pattern_type:
            return [p for p in self._patterns if p.pattern_type == pattern_type]
        return list(self._patterns)

    @property
    def pattern_count(self) -> int:
        return len(self._patterns)

    @property
    def detection_count(self) -> int:
        return self._detection_count
