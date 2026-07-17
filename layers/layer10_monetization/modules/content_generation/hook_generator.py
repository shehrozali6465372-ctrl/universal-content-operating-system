"""HookGenerator — Generate engaging hooks and openings."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_HG_COUNTER = itertools.count(1)


class Hook:
    """A generated content hook."""

    __slots__ = ("hook_id", "text", "hook_type", "platform", "score")

    def __init__(self, text: str = "", hook_type: str = "") -> None:
        self.hook_id: str = f"hook_{next(_HG_COUNTER)}"
        self.text = text
        self.hook_type = hook_type
        self.platform: str = ""
        self.score: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {"hook_id": self.hook_id, "text": self.text,
                "hook_type": self.hook_type, "score": round(self.score, 3)}


HOOK_TEMPLATES = {
    "question": ["Did you know {topic}?", "What if {topic}?", "Have you tried {topic}?"],
    "statistic": ["95% of {topic} fail because...", "{topic} increased by 300%..."],
    "story": ["I tried {topic} for 30 days. Here's what happened.", "My journey with {topic}."],
    "controversy": ["Unpopular opinion: {topic} is overrated.", "Why everyone is wrong about {topic}."],
    "listicle": ["7 secrets about {topic} nobody tells you.", "Top 5 {topic} tips."],
    "how_to": ["How to master {topic} in 2024.", "The ultimate guide to {topic}."],
}


class HookGenerator:
    """Generate engaging hooks for content."""

    def __init__(self) -> None:
        self._hooks: List[Hook] = []

    def generate(self, topic: str, hook_type: str = "question",
                 platform: str = "", count: int = 3) -> List[Hook]:
        templates = HOOK_TEMPLATES.get(hook_type, HOOK_TEMPLATES["question"])
        generated = []
        for template in templates[:count]:
            hook = Hook(template.format(topic=topic), hook_type)
            hook.platform = platform
            hook.score = 0.5 + (hash(topic) % 50) / 100
            self._hooks.append(hook)
            generated.append(hook)
        return generated

    def generate_batch(self, topic: str, platform: str = "") -> List[Hook]:
        all_hooks = []
        for hook_type in HOOK_TEMPLATES:
            all_hooks.extend(self.generate(topic, hook_type, platform, count=1))
        return all_hooks

    def get_best_hooks(self, count: int = 5) -> List[Hook]:
        return sorted(self._hooks, key=lambda h: h.score, reverse=True)[:count]

    def get_stats(self) -> Dict[str, Any]:
        types = {}
        for h in self._hooks:
            types[h.hook_type] = types.get(h.hook_type, 0) + 1
        return {"total": len(self._hooks), "by_type": types}
