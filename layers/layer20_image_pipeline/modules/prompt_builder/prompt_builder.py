"""PromptBuilder — build optimized image generation prompts."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class ImagePrompt:
    __slots__ = ("prompt_id", "positive", "negative", "style", "parameters",
                 "platform", "metadata")

    def __init__(self, positive: str = "", negative: str = "") -> None:
        self.prompt_id = f"imgprompt_{id(self) % 100000}"
        self.positive = positive
        self.negative = negative
        self.style = ""
        self.parameters: Dict[str, Any] = {}
        self.platform = ""
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"prompt_id": self.prompt_id, "positive": self.positive,
                "negative": self.negative, "style": self.style,
                "platform": self.platform}


class PromptBuilder:
    def __init__(self) -> None:
        self._templates: Dict[str, str] = {}
        self._styles: Dict[str, str] = {
            "photorealistic": "highly detailed, photorealistic, 8k",
            "illustration": "digital illustration, vibrant colors, clean lines",
            "minimalist": "minimalist, clean design, white background",
            "cinematic": "cinematic lighting, dramatic, wide angle",
        }

    def build(self, subject: str, style: str = "photorealistic",
              platform: str = "instagram", extra_tags: Optional[List[str]] = None) -> ImagePrompt:
        style_suffix = self._styles.get(style, style)
        prompt_text = f"{subject}, {style_suffix}"
        if extra_tags:
            prompt_text += ", " + ", ".join(extra_tags)
        prompt = ImagePrompt(prompt_text)
        prompt.style = style
        prompt.platform = platform
        prompt.parameters = {"quality": "high", "aspect_ratio": "1:1"}
        return prompt

    def add_template(self, name: str, template: str) -> None:
        self._templates[name] = template

    def add_style(self, name: str, suffix: str) -> None:
        self._styles[name] = suffix

    def from_template(self, template_name: str, **kwargs: Any) -> ImagePrompt:
        template = self._templates.get(template_name, "")
        text = template.format(**kwargs) if kwargs else template
        return ImagePrompt(text)

    def optimize_for_platform(self, prompt: ImagePrompt, platform: str) -> ImagePrompt:
        prompt.platform = platform
        if platform == "linkedin":
            prompt.parameters["aspect_ratio"] = "1.91:1"
        elif platform in ("instagram", "facebook"):
            prompt.parameters["aspect_ratio"] = "1:1"
        elif platform == "youtube":
            prompt.parameters["aspect_ratio"] = "16:9"
        elif platform == "pinterest":
            prompt.parameters["aspect_ratio"] = "2:3"
        return prompt

    def list_styles(self) -> List[str]:
        return list(self._styles.keys())

    def list_templates(self) -> List[str]:
        return list(self._templates.keys())
