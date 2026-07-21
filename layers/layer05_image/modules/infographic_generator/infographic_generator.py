"""InfographicGenerator — Create professional infographics for social media."""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class InfographicItem:
    __slots__ = ("number", "title", "description", "color", "icon")

    def __init__(self, number: int, title: str, description: str,
                 color: str = "#FFD700", icon: str = "") -> None:
        self.number = number
        self.title = title
        self.description = description
        self.color = color
        self.icon = icon


class InfographicConfig:
    __slots__ = ("width", "height", "bg_color", "header_color",
                 "footer_color", "title_color", "text_color",
                 "subtitle_color", "brand_name", "font_dir")

    def __init__(self) -> None:
        self.width = 1080
        self.height = 1080
        self.bg_color = "#0D1B2A"
        self.header_color = "#1A237E"
        self.footer_color = "#1A237E"
        self.title_color = "#FFD700"
        self.text_color = "#FFFFFF"
        self.subtitle_color = "#B0BEC5"
        self.brand_name = "deeplora"
        self.font_dir = "/usr/share/fonts/truetype/dejavu/"


class InfographicGenerator:
    COLORS = ["#FFD700", "#4FC3F7", "#26C6DA", "#66BB6A", "#FFA726",
              "#EF5350", "#AB47BC", "#5C6BC0"]

    def __init__(self, config: Optional[InfographicConfig] = None) -> None:
        self._config = config or InfographicConfig()
        self._fonts: Dict[str, Any] = {}

    def generate(self, title: str, subtitle: str, items: List[InfographicItem],
                 footer: str = "", output_path: str = "/tmp/infographic.png") -> str:
        if not PILLOW_AVAILABLE:
            raise RuntimeError("Pillow not installed")

        cfg = self._config
        img = Image.new("RGB", (cfg.width, cfg.height), cfg.bg_color)
        draw = ImageDraw.Draw(img)
        fonts = self._load_fonts()

        header_h = 120
        draw.rectangle([0, 0, cfg.width, header_h], fill=cfg.header_color)
        draw.text((cfg.width // 2, 25), title, fill=cfg.title_color,
                  font=fonts["medium"], anchor="mt")
        draw.text((cfg.width // 2, 70), subtitle, fill=cfg.text_color,
                  font=fonts["small"], anchor="mt")
        draw.line([(60, header_h + 10), (cfg.width - 60, header_h + 10)],
                  fill=cfg.title_color, width=2)

        y_start = header_h + 30
        item_h = max(140, (cfg.height - header_h - 120) // max(len(items), 1))

        for i, item in enumerate(items):
            y = y_start + i * item_h
            color = item.color or self.COLORS[i % len(self.COLORS)]
            cx, cy = 80, y + 45
            draw.ellipse([cx - 28, cy - 28, cx + 28, cy + 28], fill=color)
            draw.text((cx, cy), str(item.number), fill="#0D1B2A",
                      font=fonts["large"], anchor="mm")
            draw.text((130, y + 8), item.title, fill=color, font=fonts["medium"])
            desc = item.description
            if len(desc) > 70:
                mid = desc[:70].rfind(" ")
                if mid < 0:
                    mid = 70
                draw.text((130, y + 45), desc[:mid], fill=cfg.text_color,
                          font=fonts["small"])
                draw.text((130, y + 75), desc[mid:].strip(),
                          fill=cfg.subtitle_color, font=fonts["small"])
            else:
                draw.text((130, y + 45), desc, fill=cfg.text_color,
                          font=fonts["small"])
            if i < len(items) - 1:
                draw.line([(130, y + item_h - 8), (cfg.width - 60, y + item_h - 8)],
                          fill="#1E3A5F", width=1)

        footer_y = cfg.height - 100
        draw.rectangle([0, footer_y, cfg.width, cfg.height], fill=cfg.footer_color)
        if footer:
            draw.text((cfg.width // 2, footer_y + 15), footer,
                      fill=cfg.title_color, font=fonts["small"], anchor="mt")
        draw.text((cfg.width // 2, footer_y + 50),
                  "Which one amazed you the most? Comment below!",
                  fill=cfg.text_color, font=fonts["small"], anchor="mt")
        draw.text((cfg.width - 20, footer_y - 25), cfg.brand_name,
                  fill="#4FC3F7", font=fonts["small"], anchor="rt")

        img.save(output_path, "PNG", quality=95)
        return output_path

    def generate_from_list(self, title: str, subtitle: str,
                           items: List[Dict[str, str]],
                           footer: str = "",
                           output_path: str = "/tmp/infographic.png") -> str:
        infographic_items = []
        for i, item in enumerate(items):
            infographic_items.append(InfographicItem(
                number=i + 1, title=item.get("title", ""),
                description=item.get("description", ""),
                color=item.get("color", self.COLORS[i % len(self.COLORS)]),
            ))
        return self.generate(title, subtitle, infographic_items, footer, output_path)

    def _load_fonts(self) -> Dict[str, Any]:
        if self._fonts:
            return self._fonts
        fd = self._config.font_dir
        try:
            self._fonts = {
                "large": ImageFont.truetype(f"{fd}DejaVuSans-Bold.ttf", 38),
                "medium": ImageFont.truetype(f"{fd}DejaVuSans-Bold.ttf", 26),
                "small": ImageFont.truetype(f"{fd}DejaVuSans.ttf", 20),
            }
        except Exception:
            default = ImageFont.load_default()
            self._fonts = {"large": default, "medium": default, "small": default}
        return self._fonts
