"""Production-safe image prompt construction."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid

class ImagePrompt:
    __slots__=("prompt_id","positive","negative","style","parameters","platform","metadata")
    def __init__(self, positive: str="", negative: str="") -> None:
        self.prompt_id=f"imgprompt_{uuid.uuid4().hex}"; self.positive=positive; self.negative=negative
        self.style=""; self.parameters: Dict[str,Any]={}; self.platform=""; self.metadata: Dict[str,Any]={}
    def to_dict(self) -> Dict[str,Any]:
        return {"prompt_id":self.prompt_id,"positive":self.positive,"negative":self.negative,
                "style":self.style,"platform":self.platform,"parameters":dict(self.parameters),"metadata":dict(self.metadata)}

class PromptBuilder:
    def __init__(self) -> None:
        self._templates: Dict[str,str]={}
        self._styles={"photorealistic":"highly detailed, photorealistic, 8k","illustration":"digital illustration, vibrant colors, clean lines",
                      "minimalist":"minimalist, clean design, white background","cinematic":"cinematic lighting, dramatic, wide angle"}
    def build(self, subject: str, style: str="photorealistic", platform: str="instagram",
              extra_tags: Optional[List[str]]=None) -> ImagePrompt:
        if not isinstance(subject,str) or not subject.strip(): raise ValueError("subject is required")
        if not isinstance(style,str) or not style.strip(): raise ValueError("style is required")
        if not isinstance(platform,str) or not platform.strip(): raise ValueError("platform is required")
        if extra_tags is not None and any(not isinstance(t,str) or not t.strip() for t in extra_tags):
            raise ValueError("extra_tags must contain non-empty strings")
        suffix=self._styles.get(style,style); text=f"{subject.strip()}, {suffix}"
        if extra_tags: text += ", " + ", ".join(t.strip() for t in extra_tags)
        prompt=ImagePrompt(text); prompt.style=style; prompt.platform=platform.strip().lower()
        prompt.parameters={"quality":"high","aspect_ratio":"1:1"}; return prompt
    def add_template(self,name: str,template: str) -> None:
        if not name or not name.strip(): raise ValueError("template name is required")
        if not isinstance(template,str): raise TypeError("template must be a string")
        self._templates[name]=template
    def add_style(self,name: str,suffix: str) -> None:
        if not name or not name.strip(): raise ValueError("style name is required")
        if not isinstance(suffix,str) or not suffix.strip(): raise ValueError("style suffix is required")
        self._styles[name]=suffix
    def from_template(self,template_name: str,**kwargs: Any) -> ImagePrompt:
        if template_name not in self._templates: raise KeyError(f"unknown template: {template_name}")
        try: text=self._templates[template_name].format(**kwargs)
        except (KeyError,ValueError,IndexError) as exc: raise ValueError(f"template rendering failed: {exc}") from exc
        return ImagePrompt(text)
    def optimize_for_platform(self,prompt: ImagePrompt,platform: str) -> ImagePrompt:
        if not isinstance(prompt,ImagePrompt): raise TypeError("prompt must be an ImagePrompt")
        if not isinstance(platform,str) or not platform.strip(): raise ValueError("platform is required")
        normalized=platform.strip().lower(); prompt.platform=normalized
        ratio={"linkedin":"1.91:1","instagram":"1:1","facebook":"1:1","youtube":"16:9","pinterest":"2:3"}.get(normalized)
        if ratio: prompt.parameters["aspect_ratio"]=ratio
        return prompt
    def list_styles(self) -> List[str]: return list(self._styles.keys())
    def list_templates(self) -> List[str]: return list(self._templates.keys())
