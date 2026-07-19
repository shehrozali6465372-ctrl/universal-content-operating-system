"""StyleEngine — manage and apply visual styles to images."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class StylePreset:
    __slots__ = ("name", "colors", "fonts", "effects", "metadata")

    def __init__(self, name: str, colors: Optional[List[str]] = None,
                 fonts: Optional[List[str]] = None,
                 effects: Optional[List[str]] = None) -> None:
        self.name = name
        self.colors = colors or []
        self.fonts = fonts or []
        self.effects = effects or []
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "colors": self.colors,
                "fonts": self.fonts, "effects": self.effects}


class StyleEngine:
    def __init__(self) -> None:
        self._presets: Dict[str, StylePreset] = {}
        self._brand_style: Optional[StylePreset] = None

    def add_preset(self, preset: StylePreset) -> None:
        self._presets[preset.name] = preset

    def get_preset(self, name: str) -> Optional[StylePreset]:
        return self._presets.get(name)

    def set_brand_style(self, preset: StylePreset) -> None:
        self._brand_style = preset

    def get_brand_style(self) -> Optional[StylePreset]:
        return self._brand_style

    def apply_style(self, content: Dict[str, Any], style_name: str) -> Dict[str, Any]:
        preset = self._presets.get(style_name)
        if not preset:
            return content
        result = dict(content)
        result["style"] = preset.to_dict()
        return result

    def list_presets(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._presets.values()]

    def suggest_style(self, platform: str, content_type: str = "post") -> str:
        suggestions = {
            ("instagram", "post"): "photorealistic",
            ("linkedin", "post"): "minimalist",
            ("youtube", "thumbnail"): "cinematic",
            ("twitter", "post"): "illustration",
        }
        return suggestions.get((platform, content_type), "photorealistic")
