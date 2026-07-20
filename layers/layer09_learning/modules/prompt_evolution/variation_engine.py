"""VariationEngine — Generates A/B test variants of prompt templates.

Takes a base template and generates multiple variations by:
- Changing hook types
- Changing CTA types
- Adjusting tone/style
- Mixing successful patterns from other templates
"""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
from layers.layer09_learning.modules.prompt_evolution.style_library import StyleLibrary


class VariationEngine:
    """Generates A/B test variants of prompt templates."""

    def __init__(self, style_library: Optional[StyleLibrary] = None) -> None:
        self._styles = style_library or StyleLibrary()
        self._variation_count = 0

    def generate_variations(
        self,
        base: PromptTemplate,
        count: int = 3,
        strategy: str = "mixed",
    ) -> List[PromptTemplate]:
        """Generate multiple variations of a template.

        Strategies:
        - "hook": Vary only the hook type
        - "cta": Vary only the CTA type
        - "tone": Vary tone and style
        - "mixed": Mix of all strategies
        """
        variations = []
        strategies = self._get_strategy_list(strategy, count)

        for i in range(count):
            variant = base.clone()
            strat = strategies[i % len(strategies)]

            if strat == "hook":
                variant.hook_type = self._vary_hook_type(base.hook_type)
                variant.hook_template = self._generate_hook(variant)
            elif strat == "cta":
                variant.cta_type = self._vary_cta_type(base.cta_type)
                variant.cta_template = self._generate_cta(variant)
            elif strat == "tone":
                variant.tone = self._vary_tone(base.tone)
                variant.style = self._vary_style(base.style)
            else:  # mixed
                variant.hook_type = self._vary_hook_type(base.hook_type)
                variant.cta_type = self._vary_cta_type(base.cta_type)
                variant.hook_template = self._generate_hook(variant)
                variant.cta_template = self._generate_cta(variant)

            variant.tags = list(base.tags) + [f"variant_{strat}", f"gen_{variant.generation}"]
            variant.metadata["variation_strategy"] = strat
            variant.metadata["base_id"] = base.template_id
            variations.append(variant)
            self._variation_count += 1

        return variations

    def generate_ab_test(
        self,
        champion: PromptTemplate,
        count: int = 2,
    ) -> List[PromptTemplate]:
        """Generate challenger variants to test against the champion."""
        challengers = []
        strategies = ["hook", "cta", "mixed"]

        for i in range(count):
            variant = champion.clone()
            strat = strategies[i % len(strategies)]

            if strat == "hook":
                variant.hook_type = self._vary_hook_type(champion.hook_type)
                variant.hook_template = self._generate_hook(variant)
                variant.tags.append("ab_test_hook")
            elif strat == "cta":
                variant.cta_type = self._vary_cta_type(champion.cta_type)
                variant.cta_template = self._generate_cta(variant)
                variant.tags.append("ab_test_cta")
            else:
                variant.hook_type = self._vary_hook_type(champion.hook_type)
                variant.cta_type = self._vary_cta_type(champion.cta_type)
                variant.hook_template = self._generate_hook(variant)
                variant.cta_template = self._generate_cta(variant)
                variant.tags.append("ab_test_mixed")

            variant.tags.append("challenger")
            variant.metadata["ab_test"] = True
            variant.metadata["champion_id"] = champion.template_id
            challengers.append(variant)
            self._variation_count += 1

        return challengers

    def generate_from_style(
        self,
        topic: str,
        platform: str,
        style_name: str,
    ) -> PromptTemplate:
        """Generate a fresh template from a style library entry."""
        style = self._styles.get_style(style_name)
        hook = self._styles.get_random_hook(style_name)
        cta = self._styles.get_random_cta(style_name)

        tpl = PromptTemplate(
            topic=topic, platform=platform,
            tone=style.get("tone_guidelines", "professional").split(".")[0],
            style=style.get("category", "educational"),
        )
        tpl.hook_template = hook
        tpl.cta_template = cta
        tpl.body_template = "{hook}\n\n{body}\n\n{cta}"
        tpl.tags = [style_name, platform, "auto_generated"]
        return tpl

    def _vary_hook_type(self, current: str) -> str:
        """Pick a different hook type."""
        hook_types = ["question", "statistic", "story", "bold_claim",
                      "how_to", "list", "comparison", "curiosity_gap"]
        alternatives = [h for h in hook_types if h != current]
        return random.choice(alternatives) if alternatives else current

    def _vary_cta_type(self, current: str) -> str:
        """Pick a different CTA type."""
        cta_types = ["ask_question", "share_opinion", "save_post",
                     "follow", "comment", "tag_friend"]
        alternatives = [c for c in cta_types if c != current]
        return random.choice(alternatives) if alternatives else current

    def _vary_tone(self, current: str) -> str:
        """Pick a different tone."""
        tones = ["professional", "casual", "bold", "inspiring",
                 "educational", "entertaining", "controversial"]
        alternatives = [t for t in tones if t != current]
        return random.choice(alternatives) if alternatives else current

    def _vary_style(self, current: str) -> str:
        """Pick a different style."""
        styles = ["educational", "entertaining", "engaging",
                  "thought_leadership", "viral", "storytelling"]
        alternatives = [s for s in styles if s != current]
        return random.choice(alternatives) if alternatives else current

    def _generate_hook(self, template: PromptTemplate) -> str:
        """Generate a hook string based on hook type."""
        topic = template.topic or "this topic"
        hooks = {
            "question": f"Did you know about {topic}?",
            "statistic": f"87% of people don't know this about {topic}.",
            "story": f"Here's a story about {topic} that will surprise you:",
            "bold_claim": f"{topic} is about to change everything.",
            "how_to": f"Here's how to master {topic}:",
            "list": f"5 things about {topic} you need to know:",
            "comparison": f"{topic} vs. what you think you know:",
            "curiosity_gap": f"The one thing about {topic} nobody talks about:",
            "testimonial": f"I tried {topic} for 30 days. Here's what happened:",
            "controversial": f"Unpopular opinion: {topic} is overrated.",
        }
        return hooks.get(template.hook_type, f"Let's talk about {topic}.")

    def _generate_cta(self, template: PromptTemplate) -> str:
        """Generate a CTA string based on CTA type."""
        ctas = {
            "ask_question": "What do you think? Share your thoughts below!",
            "share_opinion": "Agree or disagree? Let me know!",
            "save_post": "Save this post for later! 🔖",
            "follow": "Follow for more insights like this!",
            "comment": "Drop a comment with your experience!",
            "tag_friend": "Tag someone who needs to see this!",
            "link_bio": "Check the link in bio for more!",
            "dm_me": "DM me 'GUIDE' for the full version!",
            "swipe_up": "Swipe up to learn more!",
            "learn_more": "Click the link to dive deeper!",
        }
        return ctas.get(template.cta_type, "What do you think?")

    def _get_strategy_list(self, strategy: str, count: int) -> List[str]:
        """Get a list of strategies for generating variations."""
        if strategy == "hook":
            return ["hook"] * count
        elif strategy == "cta":
            return ["cta"] * count
        elif strategy == "tone":
            return ["tone"] * count
        else:  # mixed
            pool = ["hook", "cta", "tone", "mixed"]
            return [random.choice(pool) for _ in range(count)]

    @property
    def total_variations(self) -> int:
        return self._variation_count
