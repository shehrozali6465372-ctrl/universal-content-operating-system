"""Emotional Analyzer - Detects emotional tone and sentiment intensity."""
from __future__ import annotations
from typing import Dict, List


class EmotionScore:
    __slots__ = ("emotion", "score", "intensity")
    def __init__(self, emotion: str = "", score: float = 0.0, intensity: str = "low"):
        self.emotion = emotion
        self.score = score
        self.intensity = intensity
    def to_dict(self) -> Dict:
        return {"emotion": self.emotion, "score": round(self.score, 3), "intensity": self.intensity}


class EmotionalResult:
    __slots__ = ("dominant_emotion", "emotions", "sentiment", "sentiment_score",
                 "emotional_intensity", "tone")
    def __init__(self) -> None:
        self.dominant_emotion = ""
        self.emotions: List[EmotionScore] = []
        self.sentiment = "neutral"
        self.sentiment_score = 0.0
        self.emotional_intensity = 0.0
        self.tone = ""
    def to_dict(self) -> Dict:
        return {
            "dominant_emotion": self.dominant_emotion,
            "emotions": [e.to_dict() for e in self.emotions],
            "sentiment": self.sentiment, "sentiment_score": round(self.sentiment_score, 3),
            "emotional_intensity": round(self.emotional_intensity, 3), "tone": self.tone,
        }


_EMOTION_LEXICON = {
    "joy": {"happy", "great", "amazing", "wonderful", "love", "excellent", "fantastic", "beautiful", "best", "celebrate", "excited", "awesome"},
    "sadness": {"sad", "unfortunate", "terrible", "horrible", "worst", "disappointing", "tragic", "loss", "grief", "miserable"},
    "anger": {"angry", "furious", "outrage", "unacceptable", "corruption", "scam", "fraud", "betray", "exploit"},
    "fear": {"fear", "afraid", "danger", "threat", "risk", "worry", "anxious", "concern", "panic", "crisis"},
    "surprise": {"surprising", "unexpected", "shocking", "incredible", "unbelievable", "astonishing", "stunning"},
    "trust": {"trust", "reliable", "credible", "honest", "integrity", "transparent", "dependable"},
    "anticipation": {"hope", "excited", "looking forward", "upcoming", "soon", "future", "expect"},
}
_POSITIVE_WORDS = {"good", "great", "best", "amazing", "wonderful", "love", "excellent", "happy", "beautiful", "fantastic", "awesome", "brilliant", "perfect", "outstanding", "superb"}
_NEGATIVE_WORDS = {"bad", "worst", "terrible", "horrible", "hate", "ugly", "awful", "sad", "angry", "danger", "crisis", "fail", "loss", "poor", "weak"}


class EmotionalAnalyzer:
    def analyze(self, text: str) -> EmotionalResult:
        result = EmotionalResult()
        words = set(w.lower().strip(".,!?;:") for w in text.split())
        emotion_scores = {}
        for emotion, lexicon in _EMOTION_LEXICON.items():
            matches = len(words & lexicon)
            if matches > 0:
                emotion_scores[emotion] = min(1.0, matches / 3.0)
        for emotion, score in sorted(emotion_scores.items(), key=lambda x: -x[1]):
            intensity = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
            result.emotions.append(EmotionScore(emotion, score, intensity))
        if result.emotions:
            result.dominant_emotion = result.emotions[0].emotion
            result.emotional_intensity = result.emotions[0].score
        pos = len(words & _POSITIVE_WORDS)
        neg = len(words & _NEGATIVE_WORDS)
        total = pos + neg
        if total > 0:
            result.sentiment_score = (pos - neg) / total
            if result.sentiment_score > 0.2: result.sentiment = "positive"
            elif result.sentiment_score < -0.2: result.sentiment = "negative"
            else: result.sentiment = "neutral"
        if result.dominant_emotion in ("joy", "trust"): result.tone = "uplifting"
        elif result.dominant_emotion in ("sadness", "fear"): result.tone = "concerning"
        elif result.dominant_emotion == "anger": result.tone = "critical"
        elif result.dominant_emotion == "surprise": result.tone = "startling"
        else: result.tone = "neutral"
        return result
