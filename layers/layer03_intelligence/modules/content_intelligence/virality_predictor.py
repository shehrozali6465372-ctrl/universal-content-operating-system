"""Content Virality Predictor - Predicts content viral potential."""
from __future__ import annotations
from typing import Dict, List


class ContentViralityResult:
    __slots__ = ("virality_score", "factors", "shareability", "hook_strength",
                 "emotional_trigger", "uniqueness", "recommendations")
    def __init__(self) -> None:
        self.virality_score = 0.0
        self.factors: Dict[str, float] = {}
        self.shareability = 0.0
        self.hook_strength = 0.0
        self.emotional_trigger = 0.0
        self.uniqueness = 0.0
        self.recommendations: List[str] = []
    def to_dict(self) -> Dict:
        return {
            "virality_score": round(self.virality_score, 3),
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
            "shareability": round(self.shareability, 3),
            "hook_strength": round(self.hook_strength, 3),
            "emotional_trigger": round(self.emotional_trigger, 3),
            "uniqueness": round(self.uniqueness, 3),
            "recommendations": list(self.recommendations),
        }


class ContentViralityPredictor:
    def predict(self, content: str, metadata: Dict = None) -> ContentViralityResult:
        result = ContentViralityResult()
        first_sentence = content.split(".")[0] if "." in content else content[:100]
        hook_words = {"how", "why", "secret", "amazing", "shocking", "never", "always", "best", "worst"}
        result.hook_strength = min(1.0, sum(1 for w in first_sentence.lower().split() if w in hook_words) / 3.0)
        emotional_words = {"love", "hate", "amazing", "terrible", "shocking", "incredible", "urgent", "breaking"}
        content_words = set(w.lower() for w in content.split())
        result.emotional_trigger = min(1.0, len(content_words & emotional_words) / 3.0)
        words = content.split()
        result.uniqueness = min(1.0, len(set(w.lower() for w in words)) / max(len(words), 1) + 0.2)
        has_list = any(c in content for c in ["1.", "2.", "-", chr(8226)])
        share_base = 0.3
        if has_list: share_base += 0.2
        if 100 < len(content) < 2000: share_base += 0.2
        result.shareability = min(1.0, share_base)
        result.factors = {"hook": result.hook_strength, "emotion": result.emotional_trigger,
                         "uniqueness": result.uniqueness, "shareability": result.shareability}
        result.virality_score = (result.hook_strength * 0.25 + result.emotional_trigger * 0.3
                               + result.uniqueness * 0.2 + result.shareability * 0.25)
        if result.hook_strength < 0.3: result.recommendations.append("Strengthen the opening hook")
        if result.emotional_trigger < 0.3: result.recommendations.append("Add emotional triggers")
        if result.shareability < 0.5: result.recommendations.append("Improve shareability")
        return result
