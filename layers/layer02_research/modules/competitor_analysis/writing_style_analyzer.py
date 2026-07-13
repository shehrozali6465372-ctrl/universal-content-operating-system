"""
Writing Style Analyzer
Layer 2: Research Engine — Module 3

Analyzes competitor writing patterns:
- Tone and voice detection
- Readability scoring
- Vocabulary analysis
- CTA patterns
- Emoji usage
- Post length preferences
"""

from collections import Counter
from typing import Dict, List, Optional, Tuple
import re


class WritingStyleProfile:
    """Analyzed writing style for a competitor."""

    __slots__ = (
        "competitor_id", "avg_word_count", "avg_sentence_length",
        "avg_paragraph_count", "readability_score",
        "tone", "voice", "formality_level",
        "common_words", "common_phrases", "cta_patterns",
        "emoji_frequency", "question_frequency",
        "exclamation_frequency", "hashtag_density",
        "link_frequency", "post_length_category",
    )

    TONE_LABELS = ["professional", "casual", "humorous", "educational", "inspirational", "aggressive", "neutral"]
    FORMALITY_LEVELS = ["formal", "semi_formal", "casual", "very_casual"]

    def __init__(self, competitor_id: str):
        self.competitor_id = competitor_id
        self.avg_word_count = 0.0
        self.avg_sentence_length = 0.0
        self.avg_paragraph_count = 0.0
        self.readability_score = 0.0
        self.tone = "neutral"
        self.voice = "third_person"
        self.formality_level = "semi_formal"
        self.common_words: List[Tuple[str, int]] = []
        self.common_phrases: List[Tuple[str, int]] = []
        self.cta_patterns: List[str] = []
        self.emoji_frequency = 0.0
        self.question_frequency = 0.0
        self.exclamation_frequency = 0.0
        self.hashtag_density = 0.0
        self.link_frequency = 0.0
        self.post_length_category = "medium"

    def to_dict(self) -> dict:
        return {
            "competitor_id": self.competitor_id,
            "avg_word_count": self.avg_word_count,
            "avg_sentence_length": self.avg_sentence_length,
            "avg_paragraph_count": self.avg_paragraph_count,
            "readability_score": self.readability_score,
            "tone": self.tone,
            "voice": self.voice,
            "formality_level": self.formality_level,
            "common_words": self.common_words[:20],
            "cta_patterns": self.cta_patterns,
            "emoji_frequency": self.emoji_frequency,
            "question_frequency": self.question_frequency,
            "exclamation_frequency": self.exclamation_frequency,
            "hashtag_density": self.hashtag_density,
            "post_length_category": self.post_length_category,
        }


# Common CTA patterns
CTA_KEYWORDS = [
    "click here", "sign up", "learn more", "join now", "get started",
    "buy now", "shop now", "try free", "subscribe", "follow us",
    "share this", "tag a friend", "drop a comment", "dm us",
    "link in bio", "swipe up", "comment below", "tell us",
    "what do you think", "save this", "don't miss",
]

# Emoji regex
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "]+",
    flags=re.UNICODE,
)


class WritingStyleAnalyzer:
    """Analyze writing style of competitor posts."""

    def __init__(self):
        self._profiles: Dict[str, WritingStyleProfile] = {}

    def analyze(
        self,
        competitor_id: str,
        texts: List[str],
        hashtags_per_post: Optional[List[List[str]]] = None,
    ) -> WritingStyleProfile:
        """Full writing style analysis from post texts."""
        profile = WritingStyleProfile(competitor_id)

        if not texts:
            self._profiles[competitor_id] = profile
            return profile

        word_counts = []
        sentence_counts = []
        paragraph_counts = []
        emojis_total = 0
        questions_total = 0
        exclamations_total = 0
        hashtags_total = 0
        links_total = 0
        all_words = []

        for text in texts:
            words = text.split()
            word_counts.append(len(words))
            all_words.extend(w.lower() for w in words if len(w) > 2)

            # Sentences (by punctuation)
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
            sentence_counts.append(len(sentences))

            # Paragraphs (by double newline or line breaks)
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\n', text) if p.strip()]
            paragraph_counts.append(len(paragraphs))

            # Emoji count
            emojis_total += len(EMOJI_PATTERN.findall(text))

            # Questions
            questions_total += text.count('?')

            # Exclamations
            exclamations_total += text.count('!')

            # Links
            if 'http' in text or 'www.' in text:
                links_total += 1

        n = len(texts)
        profile.avg_word_count = round(sum(word_counts) / n, 1)
        profile.avg_sentence_length = round(
            sum(word_counts) / max(sum(sentence_counts), 1), 1
        )
        profile.avg_paragraph_count = round(sum(paragraph_counts) / n, 1)

        # Post length category
        if profile.avg_word_count < 30:
            profile.post_length_category = "short"
        elif profile.avg_word_count < 100:
            profile.post_length_category = "medium"
        elif profile.avg_word_count < 300:
            profile.post_length_category = "long"
        else:
            profile.post_length_category = "very_long"

        # Emoji frequency (per post)
        profile.emoji_frequency = round(emojis_total / n, 2)
        profile.question_frequency = round(questions_total / n, 2)
        profile.exclamation_frequency = round(exclamations_total / n, 2)

        # Hashtag density
        if hashtags_per_post:
            hashtags_total = sum(len(h) for h in hashtags_per_post)
            profile.hashtag_density = round(hashtags_total / n, 2)

        # Link frequency
        profile.link_frequency = round(links_total / n * 100, 1)

        # Common words
        word_freq = Counter(all_words)
        profile.common_words = word_freq.most_common(20)

        # Tone detection
        profile.tone = self._detect_tone(texts)

        # Voice
        profile.voice = self._detect_voice(texts)

        # Formality
        profile.formality_level = self._detect_formality(profile)

        # Readability (simplified Flesch)
        profile.readability_score = self._calculate_readability(
            word_counts, sentence_counts
        )

        # CTA patterns
        profile.cta_patterns = self._find_cta_patterns(texts)

        self._profiles[competitor_id] = profile
        return profile

    def get_profile(self, competitor_id: str) -> Optional[WritingStyleProfile]:
        return self._profiles.get(competitor_id)

    def _detect_tone(self, texts: List[str]) -> str:
        """Simple tone detection based on word patterns."""
        combined = " ".join(texts).lower()

        humor_words = ["lol", "haha", "funny", "joke", "😂", "🤣", "meme"]
        edu_words = ["learn", "tutorial", "how to", "guide", "tip", "explain"]
        pro_words = ["professional", "business", "strategy", "solution", "enterprise"]
        inspire_words = ["inspire", "motivation", "believe", "dream", "achieve", "success"]

        scores = {
            "humorous": sum(combined.count(w) for w in humor_words),
            "educational": sum(combined.count(w) for w in edu_words),
            "professional": sum(combined.count(w) for w in pro_words),
            "inspirational": sum(combined.count(w) for w in inspire_words),
        }

        if max(scores.values()) == 0:
            return "neutral"
        return max(scores, key=scores.get)

    def _detect_voice(self, texts: List[str]) -> str:
        """Detect first/second/third person voice."""
        combined = " ".join(texts).lower()
        first_person = sum(combined.count(w) for w in [" i ", " we ", " our ", " us ", "my ", "me "])
        second_person = sum(combined.count(w) for w in [" you ", " your ", "yours", "yourself"])

        if second_person > first_person * 1.5:
            return "second_person"
        elif first_person > second_person * 1.5:
            return "first_person"
        return "third_person"

    def _detect_formality(self, profile: WritingStyleProfile) -> str:
        """Estimate formality from writing patterns."""
        casual_markers = profile.emoji_frequency + profile.question_frequency
        if casual_markers >= 3:
            return "very_casual"
        elif casual_markers >= 1.5:
            return "casual"
        elif profile.avg_word_count >= 100:
            return "formal"
        return "semi_formal"

    def _calculate_readability(
        self, word_counts: List[int], sentence_counts: List[int]
    ) -> float:
        """Simplified readability score (0-100)."""
        if not word_counts or not sentence_counts:
            return 50.0
        avg_words = sum(word_counts) / len(word_counts)
        avg_sentences = max(sum(sentence_counts) / len(sentence_counts), 1)
        avg_sentence_len = avg_words / avg_sentences
        # Higher = easier to read
        score = max(0, min(100, 206.835 - 1.015 * avg_sentence_len - 84.6 * (avg_words / 100)))
        return round(score, 1)

    def _find_cta_patterns(self, texts: List[str]) -> List[str]:
        """Find CTA patterns used."""
        found = set()
        combined = " ".join(texts).lower()
        for cta in CTA_KEYWORDS:
            if cta in combined:
                found.add(cta)
        return sorted(found)

    def detect_differentiation(
        self, our_profile: WritingStyleProfile, their_profile: WritingStyleProfile
    ) -> List[str]:
        """Find ways our writing can differ from competitor."""
        diffs = []
        if their_profile.tone == "professional":
            diffs.append("Use a more casual/humorous tone to stand out")
        elif their_profile.tone == "casual":
            diffs.append("Use more educational/authoritative content")

        if their_profile.post_length_category in ("long", "very_long"):
            diffs.append("Write shorter, punchier posts (they're verbose)")
        elif their_profile.post_length_category == "short":
            diffs.append("Write longer, more detailed posts (they're too brief)")

        if their_profile.emoji_frequency > 2:
            diffs.append("Use fewer emojis, more substance")
        elif their_profile.emoji_frequency < 0.5:
            diffs.append("Add emojis for visual appeal")

        if "comment below" not in their_profile.cta_patterns:
            diffs.append("Add engagement CTAs like 'comment below'")

        return diffs
