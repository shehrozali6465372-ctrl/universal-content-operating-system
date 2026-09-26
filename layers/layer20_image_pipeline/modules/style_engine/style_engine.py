"""Production-safe visual style management."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

class StylePreset:
    __slots__=("name","colors","fonts","effects","metadata")
    def __init__(self,name: str,colors: Optional[List[str]]=None,fonts: Optional[List[str]]=None,effects: Optional[List[str]]=None) -> None:
        if not name or not name.strip(): raise ValueError("style preset name is required")
        self.name=name; self.colors=list(colors or []); self.fonts=list(fonts or []); self.effects=list(effects or []); self.metadata={}
    def to_dict(self) -> Dict[str,Any]:
        return {"name":self.name,"colors":list(self.colors),"fonts":list(self.fonts),"effects":list(self.effects)}

class StyleEngine:
    def __init__(self) -> None: self._presets: Dict[str,StylePreset]={}; self._brand_style: Optional[StylePreset]=None
    def add_preset(self,preset: StylePreset) -> None:
        if not isinstance(preset,StylePreset): raise TypeError("preset must be a StylePreset")
        self._presets[preset.name]=preset
    def get_preset(self,name: str) -> Optional[StylePreset]: return self._presets.get(name)
    def set_brand_style(self,preset: StylePreset) -> None:
        if not isinstance(preset,StylePreset): raise TypeError("preset must be a StylePreset")
        self._brand_style=preset
    def get_brand_style(self) -> Optional[StylePreset]: return self._brand_style
    def apply_style(self,content: Dict[str,Any],style_name: str) -> Dict[str,Any]:
        if not isinstance(content,dict): raise TypeError("content must be a dictionary")
        if not style_name or not style_name.strip(): raise ValueError("style_name is required")
        result=dict(content); preset=self._presets.get(style_name)
        if preset is not None: result["style"]=preset.to_dict()
        return result
    def list_presets(self) -> List[Dict[str,Any]]: return [p.to_dict() for p in self._presets.values()]
    def suggest_style(self,platform: str,content_type: str="post") -> str:
        if not platform or not platform.strip(): raise ValueError("platform is required")
        suggestions={("instagram","post"):"photorealistic",("linkedin","post"):"minimalist",
                     ("youtube","thumbnail"):"cinematic",("twitter","post"):"illustration"}
        return suggestions.get((platform.strip().lower(),content_type.strip().lower()),"photorealistic")
