"""
Content Cleaner
Layer 2: Research Engine — Module 5

Cleans and normalizes collected content:
- HTML tag removal
- Whitespace normalization
- Special character handling
- Language detection (basic)
- Content truncation
- Summary generation (extractive)
"""

import re


class ContentCleaner:
    """Clean and normalize collected content."""

    # Common HTML patterns
    HTML_TAG_RE = re.compile(r'<[^>]+>')
    MULTIPLE_SPACES_RE = re.compile(r'\s+')
    SPECIAL_CHAR_RE = re.compile(r'[^\w\s.,!?:;\-]')

    @staticmethod
    def clean_html(text: str) -> str:
        """Remove HTML tags and decode entities."""
        text = ContentCleaner.HTML_TAG_RE.sub(' ', text)
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
        text = re.sub(r'&#\d+;', '', text)
        return text.strip()

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace."""
        return ContentCleaner.MULTIPLE_SPACES_RE.sub(' ', text).strip()

    @staticmethod
    def remove_special_chars(text: str, keep_basic: bool = True) -> str:
        """Remove special characters."""
        if keep_basic:
            return text
        return ContentCleaner.SPECIAL_CHAR_RE.sub('', text)

    @staticmethod
    def clean(text: str, remove_special: bool = False) -> str:
        """Full cleaning pipeline."""
        text = ContentCleaner.clean_html(text)
        text = ContentCleaner.normalize_whitespace(text)
        if remove_special:
            text = ContentCleaner.remove_special_chars(text)
        return text

    @staticmethod
    def truncate(text: str, max_words: int = 500) -> str:
        """Truncate text to max words."""
        words = text.split()
        if len(words) <= max_words:
            return text
        return ' '.join(words[:max_words]) + '...'

    @staticmethod
    def extractive_summary(text: str, sentence_count: int = 3) -> str:
        """Simple extractive summary (first N sentences)."""
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        if len(sentences) <= sentence_count:
            return text.strip()
        return ' '.join(sentences[:sentence_count])

    @staticmethod
    def detect_language(text: str) -> str:
        """Basic language detection heuristic."""
        if not text:
            return "unknown"
        # Simple word-based detection
        words = set(text.lower().split())
        english_indicators = {"the", "is", "are", "was", "were", "have", "has", "will", "can", "this"}
        spanish_indicators = {"el", "la", "es", "son", "fue", "tiene", "esto", "pero"}
        french_indicators = {"le", "la", "est", "sont", "avoir", "mais", "dans"}

        en_count = len(words & english_indicators)
        es_count = len(words & spanish_indicators)
        fr_count = len(words & french_indicators)

        if en_count > es_count and en_count > fr_count:
            return "en"
        elif es_count > fr_count:
            return "es"
        elif fr_count > 0:
            return "fr"
        return "unknown"

    @staticmethod
    def extract_urls(text: str) -> list:
        """Extract URLs from text."""
        return re.findall(r'https?://[^\s<>"]+', text)

    @staticmethod
    def extract_hashtags(text: str) -> list:
        """Extract hashtags from text."""
        return re.findall(r'#\w+', text)

    @staticmethod
    def extract_mentions(text: str) -> list:
        """Extract @mentions from text."""
        return re.findall(r'@\w+', text)
