"""Hook Engine — Generate scroll-stopping opening hooks."""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional


HOOK_TYPES = {
    "question": {
        "templates": [
            "Did you know {topic}?",
            "What if {topic} could change everything?",
            "Want to know the secret behind {topic}?",
            "Here's what nobody tells you about {topic}:",
        ],
        "best_for": ["engage", "educate"],
    },
    "statistic": {
        "templates": [
            "{stat}% of people don't realize {topic}.",
            "Only {stat}% understand the power of {topic}.",
            "Here's a shocking fact about {topic}:",
        ],
        "best_for": ["educate", "promote"],
    },
    "story": {
        "templates": [
            "3 months ago, I discovered something about {topic} that changed everything.",
            "A friend asked me about {topic}. Here's what happened next.",
            "Last week, I learned a powerful lesson about {topic}.",
        ],
        "best_for": ["inspire", "entertain"],
    },
    "provocative": {
        "templates": [
            "{topic} is a lie. Here's why.",
            "Everyone is wrong about {topic}.",
            "Unpopular opinion: {topic} isn't what you think.",
        ],
        "best_for": ["entertain", "engage"],
    },
    "howto": {
        "templates": [
            "How to master {topic} in 2026:",
            "The step-by-step guide to {topic}:",
            "Here's exactly how {topic} works:",
        ],
        "best_for": ["educate", "promote"],
    },
    "list": {
        "templates": [
            "5 things you need to know about {topic}:",
            "The top 3 {topic} mistakes (and how to fix them):",
            "{topic} essentials everyone should know:",
        ],
        "best_for": ["educate", "entertain"],
    },
}


class HookResult:
    """Generated hook with metadata."""
    __slots__ = ("hook", "hook_type", "confidence", "alternatives", "platform")

    def __init__(self) -> None:
        self.hook = ""
        self.hook_type = ""
        self.confidence = 0.5
        self.alternatives: List[str] = []
        self.platform = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hook": self.hook,
            "hook_type": self.hook_type,
            "confidence": round(self.confidence, 3),
            "alternatives": self.alternatives,
            "platform": self.platform,
        }


class HookEngine:
    """Generates scroll-stopping opening hooks."""

    def __init__(self) -> None:
        self._gen_count = 0

    def generate(self, topic: str, goal: str = "engage",
                 platform: str = "facebook", hook_type: Optional[str] = None) -> HookResult:
        """Generate a hook for the given topic."""
        result = HookResult()
        result.platform = platform

        if hook_type and hook_type in HOOK_TYPES:
            selected_type = hook_type
        else:
            selected_type = self._select_type(goal)

        result.hook_type = selected_type
        templates = HOOK_TYPES[selected_type]["templates"]
        template = random.choice(templates)
        result.hook = template.replace("{topic}", topic).replace("{stat}", str(random.randint(60, 95)))

        # Alternatives
        for alt_type in HOOK_TYPES:
            if alt_type != selected_type:
                alt_templates = HOOK_TYPES[alt_type]["templates"]
                alt = random.choice(alt_templates).replace("{topic}", topic)
                result.alternatives.append(alt)
                if len(result.alternatives) >= 3:
                    break

        result.confidence = 0.7 if goal in HOOK_TYPES[selected_type]["best_for"] else 0.5
        self._gen_count += 1
        return result

    def generate_batch(self, topic: str, count: int = 5) -> List[HookResult]:
        """Generate multiple hooks of different types."""
        results: List[HookResult] = []
        types = list(HOOK_TYPES.keys())
        for i in range(min(count, len(types))):
            results.append(self.generate(topic, hook_type=types[i]))
        return results

    def _select_type(self, goal: str) -> str:
        candidates = []
        for ht, config in HOOK_TYPES.items():
            if goal in config["best_for"]:
                candidates.append(ht)
        return random.choice(candidates) if candidates else "question"

    @property
    def generation_count(self) -> int:
        return self._gen_count
