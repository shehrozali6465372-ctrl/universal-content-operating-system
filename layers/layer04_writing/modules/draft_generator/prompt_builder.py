"""Prompt Builder — Build LLM prompts from WritingPlan."""
from __future__ import annotations
from typing import Any, Dict, Optional

from layers.layer04_writing.modules.content_planner.writing_plan import WritingPlan


class PromptSet:
    """A complete prompt set for LLM generation."""
    __slots__ = ("system_prompt", "user_prompt", "parameters", "plan_id")

    def __init__(self) -> None:
        self.system_prompt = ""
        self.user_prompt = ""
        self.parameters: Dict[str, Any] = {}
        self.plan_id = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_prompt": self.system_prompt[:200] + "..." if len(self.system_prompt) > 200 else self.system_prompt,
            "user_prompt": self.user_prompt[:200] + "..." if len(self.user_prompt) > 200 else self.user_prompt,
            "parameters": self.parameters,
            "plan_id": self.plan_id,
        }


class PromptBuilder:
    """Builds prompts from WritingPlan for LLM generation."""

    TONE_INSTRUCTIONS = {
        "friendly": "Write in a warm, approachable, and friendly tone.",
        "professional": "Write in a professional, authoritative, and polished tone.",
        "casual": "Write in a relaxed, informal, and conversational tone.",
        "informative": "Write in a clear, factual, and educational tone.",
        "humorous": "Write in a fun, witty, and entertaining tone with humor.",
        "inspiring": "Write in an uplifting, motivational, and empowering tone.",
        "enthusiastic": "Write in an energetic, excited, and passionate tone.",
        "warm": "Write in a caring, gentle, and nurturing tone.",
        "conversational": "Write as if having a friendly conversation with the reader.",
        "playful": "Write in a lighthearted, fun, and playful tone.",
    }

    GOAL_INSTRUCTIONS = {
        "educate": "Your goal is to educate the reader. Be clear, accurate, and helpful.",
        "entertain": "Your goal is to entertain the reader. Be engaging and fun.",
        "inspire": "Your goal is to inspire the reader. Be uplifting and motivational.",
        "promote": "Your goal is to promote something. Be persuasive but authentic.",
        "engage": "Your goal is to start a conversation. Ask questions and invite responses.",
    }

    STRATEGY_INSTRUCTIONS = {
        "educational": "Structure as a clear educational piece with key points.",
        "storytelling": "Tell a compelling story with a beginning, middle, and end.",
        "debate": "Present multiple perspectives on the topic fairly.",
        "news": "Report the facts clearly and concisely like a news article.",
        "tutorial": "Provide step-by-step instructions that are easy to follow.",
        "comparison": "Compare and contrast different options or approaches.",
        "case_study": "Present a real-world example with analysis and lessons.",
        "opinion": "Share a well-reasoned perspective with supporting evidence.",
        "listicle": "Organize content as an engaging numbered or bulleted list.",
        "qa": "Present content in a question-and-answer format.",
    }

    def __init__(self) -> None:
        self._prompt_count = 0

    def build(self, plan: WritingPlan, context: Optional[Dict[str, Any]] = None) -> PromptSet:
        """Build a complete prompt set from a WritingPlan."""
        ps = PromptSet()
        ps.plan_id = plan.plan_id
        ps.parameters = {
            "max_tokens": self._estimate_tokens(plan),
            "temperature": self._temperature_for_goal(plan.goal),
            "top_p": 0.9,
        }

        # System prompt
        ps.system_prompt = self._build_system_prompt(plan, context)

        # User prompt
        ps.user_prompt = self._build_user_prompt(plan, context)

        self._prompt_count += 1
        return ps

    def build_variant(self, plan: WritingPlan, variant_type: str = "alternative") -> PromptSet:
        """Build a prompt for a variant (A/B testing)."""
        ps = self.build(plan)
        if variant_type == "alternative":
            ps.user_prompt += "\n\nWrite this in a completely different style and approach than usual."
        elif variant_type == "bold":
            ps.user_prompt += "\n\nBe more bold, provocative, and attention-grabbing."
        elif variant_type == "minimal":
            ps.user_prompt += "\n\nKeep it as short and punchy as possible."
        elif variant_type == "detailed":
            ps.user_prompt += "\n\nBe more detailed and thorough with examples."
        return ps

    def _build_system_prompt(self, plan: WritingPlan, context: Optional[Dict]) -> str:
        parts = [
            "You are an expert social media content writer.",
            f"Platform: {plan.platform.title()}.",
            f"Target audience: {plan.audience}.",
            self.TONE_INSTRUCTIONS.get(plan.tone, "Write in a friendly, clear tone."),
            self.GOAL_INSTRUCTIONS.get(plan.goal, "Write engaging content."),
            self.STRATEGY_INSTRUCTIONS.get(plan.strategy, "Write well-structured content."),
        ]

        if plan.language and plan.language.lower() != "english":
            parts.append(f"Write in {plan.language}.")

        if plan.emoji_level == "high":
            parts.append("Use plenty of emojis throughout.")
        elif plan.emoji_level == "low":
            parts.append("Use minimal emojis.")
        elif plan.emoji_level == "none":
            parts.append("Do not use any emojis.")

        if plan.hashtags:
            parts.append("Include relevant hashtags at the end.")

        return "\n".join(parts)

    def _build_user_prompt(self, plan: WritingPlan, context: Optional[Dict]) -> str:
        parts = [f"Write a {plan.content_type} about: {plan.topic}"]

        if plan.length == "short":
            parts.append("Keep it under 100 words.")
        elif plan.length == "medium":
            parts.append("Aim for 150-300 words.")
        elif plan.length == "long":
            parts.append("Aim for 400-600 words with detailed explanations.")

        cta_map = {
            "engage": "End with a question to encourage engagement.",
            "share": "Encourage readers to share the post.",
            "comment": "Ask readers to leave a comment with their thoughts.",
            "visit": "Include a call-to-action to visit a link.",
            "subscribe": "Encourage readers to follow or subscribe.",
            "learn_more": "Invite readers to learn more about the topic.",
        }
        parts.append(cta_map.get(plan.cta, "End with an engaging call-to-action."))

        if context:
            if context.get("evidence"):
                parts.append(f"Use these facts: {context['evidence'][:3]}")
            if context.get("key_points"):
                parts.append(f"Cover these points: {context['key_points'][:5]}")

        return "\n".join(parts)

    def _estimate_tokens(self, plan: WritingPlan) -> int:
        token_map = {"short": 200, "medium": 500, "long": 1000}
        return token_map.get(plan.length, 500)

    def _temperature_for_goal(self, goal: str) -> float:
        temp_map = {"educate": 0.5, "entertain": 0.9, "inspire": 0.8,
                    "promote": 0.7, "engage": 0.85}
        return temp_map.get(goal, 0.7)

    @property
    def prompt_count(self) -> int:
        return self._prompt_count
