"""Image Prompt Builder — Build prompts for AI image generators."""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional

STYLE_PRESETS = {
    "modern": "Clean, modern design with bold typography and flat colors.",
    "minimalist": "Minimal design, lots of whitespace, simple elements.",
    "vibrant": "Bright, colorful, energetic visual style.",
    "professional": "Corporate, polished, trustworthy visual style.",
    "artistic": "Creative, unique, artistic visual interpretation.",
    "photorealistic": "Photorealistic, high-quality, detailed imagery.",
    "cartoon": "Fun cartoon style, playful characters and colors.",
    "neon": "Neon-lit, cyberpunk, glowing elements on dark background.",
    "watercolor": "Soft watercolor painting style, artistic and gentle.",
    "retro": "Vintage, retro design with classic color palette.",
}
SUPPORTED_PROMPT_PLATFORMS = {"facebook", "instagram", "twitter", "linkedin", "tiktok", "youtube", "pinterest", "threads"}

class ImagePrompt:
    """A prompt for AI image generation."""
    __slots__ = ("prompt_id", "text", "negative_prompt", "style", "aspect_ratio", "parameters", "provider_hint")
    def __init__(self, text: str = "") -> None:
        self.prompt_id = f"imgprompt_{uuid.uuid4().hex}"
        self.text = text
        self.negative_prompt = ""
        self.style = ""
        self.aspect_ratio = "1:1"
        self.parameters: Dict[str, Any] = {}
        self.provider_hint = ""
    def to_dict(self) -> Dict[str, Any]:
        return {"prompt_id": self.prompt_id, "text": self.text, "negative_prompt": self.negative_prompt, "style": self.style, "aspect_ratio": self.aspect_ratio, "parameters": self.parameters}

class ImagePromptBuilder:
    """Builds prompts for AI image generators."""
    def __init__(self) -> None:
        self._build_count = 0
    def build(self, description: str, style: str = "modern", platform: str = "facebook", image_type: str = "photo", extra_instructions: Optional[List[str]] = None) -> ImagePrompt:
        """Build an image generation prompt."""
        if not isinstance(description, str) or not description.strip():
            raise ValueError("description must not be empty")
        if style not in STYLE_PRESETS:
            raise ValueError(f"Unsupported image style: {style}")
        if platform not in SUPPORTED_PROMPT_PLATFORMS:
            raise ValueError(f"Unsupported image platform: {platform}")
        prompt = ImagePrompt()
        prompt.style = style
        prompt.text = f"{description.strip()}. Style: {STYLE_PRESETS[style]}"
        prompt.negative_prompt = "blurry, low quality, watermark, text errors, deformed"
        ar_map = {"facebook": "1200:630", "instagram": "1080:1080", "twitter": "16:9", "linkedin": "1200:627", "tiktok": "9:16", "youtube": "16:9", "pinterest": "2:3", "threads": "1:1"}
        prompt.aspect_ratio = ar_map[platform]
        prompt.parameters = {"quality": "hd" if style in ("photorealistic", "professional") else "standard", "size": "1024x1024"}
        if extra_instructions:
            if not isinstance(extra_instructions, list):
                raise ValueError("extra_instructions must be a list")
            prompt.text += ". " + ". ".join(str(item) for item in extra_instructions)
        self._build_count += 1
        return prompt
    def build_batch(self, descriptions: List[str], style: str = "modern", platform: str = "facebook") -> List[ImagePrompt]:
        return [self.build(d, style, platform) for d in descriptions]
    @property
    def build_count(self) -> int:
        return self._build_count
