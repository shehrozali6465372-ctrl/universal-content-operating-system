"""Layout Engine — Platform-specific image layout specifications."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


LAYOUT_PRESETS = {
    "single_focal": {"name": "Single Focal Point", "elements": ["subject", "background"], "complexity": "low"},
    "split": {"name": "Split Layout", "elements": ["left", "right"], "complexity": "medium"},
    "grid": {"name": "Grid Layout", "elements": ["cells"], "complexity": "medium"},
    "diagonal": {"name": "Diagonal Split", "elements": ["top_left", "bottom_right"], "complexity": "medium"},
    "overlay": {"name": "Text Overlay", "elements": ["image", "text_box"], "complexity": "low"},
    "multi_panel": {"name": "Multi-Panel", "elements": ["panel_1", "panel_2", "panel_3", "panel_4"], "complexity": "high"},
    "centered": {"name": "Centered Content", "elements": ["center_text", "border"], "complexity": "low"},
}


class LayoutSpec:
    """A layout specification."""
    __slots__ = ("layout_type", "width", "height", "elements", "guidelines")

    def __init__(self, layout_type: str = "centered", width: int = 1080, height: int = 1080) -> None:
        self.layout_type = layout_type
        self.width = width
        self.height = height
        preset = LAYOUT_PRESETS.get(layout_type, LAYOUT_PRESETS["centered"])
        self.elements = preset["elements"]
        self.guidelines: Dict[str, Any] = {"safe_margin": 50, "text_area_pct": 30}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layout_type": self.layout_type,
            "width": self.width,
            "height": self.height,
            "elements": self.elements,
            "guidelines": self.guidelines,
        }


class LayoutEngine:
    """Generates layout specifications for platform images."""

    def __init__(self) -> None:
        pass

    def get_layout(self, platform: str, image_type: str = "photo",
                   layout_type: Optional[str] = None) -> LayoutSpec:
        """Get a layout specification."""
        if layout_type:
            lt = layout_type
        elif image_type == "infographic":
            lt = "multi_panel"
        elif image_type == "quote":
            lt = "centered"
        elif image_type == "carousel":
            lt = "single_focal"
        else:
            lt = "centered"

        dims = {"facebook": (1200, 630), "instagram": (1080, 1080), "twitter": (1200, 675),
                "linkedin": (1200, 627), "pinterest": (1000, 1500), "youtube": (1280, 720)}
        w, h = dims.get(platform, (1080, 1080))
        return LayoutSpec(layout_type=lt, width=w, height=h)

    def get_available_layouts(self) -> List[str]:
        return list(LAYOUT_PRESETS.keys())
