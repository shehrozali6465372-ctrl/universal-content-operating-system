"""Plan Validator — Validate writing plans against rules and constraints."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer04_writing.modules.content_planner.writing_plan import WritingPlan


VALID_GOALS = {"educate", "entertain", "inspire", "promote", "engage"}
VALID_PLATFORMS = {"facebook", "instagram", "twitter", "linkedin", "youtube", "tiktok"}
VALID_TONES = {"friendly", "professional", "casual", "informative", "humorous",
               "inspiring", "enthusiastic", "warm", "conversational", "playful"}
VALID_LENGTHS = {"short", "medium", "long"}
VALID_CONTENT_TYPES = {"post", "story", "reel", "carousel", "thread", "article", "live"}
VALID_CTAS = {"engage", "share", "comment", "visit", "subscribe", "learn_more"}
VALID_STRATEGIES = {"educational", "storytelling", "debate", "news", "tutorial",
                    "comparison", "case_study", "opinion", "listicle", "qa"}
VALID_EMOJI_LEVELS = {"none", "low", "medium", "high"}


class ValidationResult:
    """Result of plan validation."""
    __slots__ = ("is_valid", "errors", "warnings", "score")

    def __init__(self) -> None:
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.score = 100.0

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False
        self.score -= 20

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)
        self.score -= 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "score": round(max(self.score, 0), 1),
        }


class PlanValidator:
    """Validates writing plans against rules."""

    def __init__(self) -> None:
        self._custom_rules: List[Any] = []

    def validate(self, plan: WritingPlan) -> ValidationResult:
        """Validate a writing plan."""
        result = ValidationResult()

        # Required fields
        if not plan.topic:
            result.add_error("Topic is required")

        # Goal validation
        if plan.goal not in VALID_GOALS:
            result.add_error(f"Invalid goal '{plan.goal}'. Must be one of: {VALID_GOALS}")

        # Platform validation
        if plan.platform not in VALID_PLATFORMS:
            result.add_error(f"Invalid platform '{plan.platform}'. Must be one of: {VALID_PLATFORMS}")

        # Tone validation
        if plan.tone not in VALID_TONES:
            result.add_warning(f"Uncommon tone '{plan.tone}'. Consider: {VALID_TONES}")

        # Length validation
        if plan.length not in VALID_LENGTHS:
            result.add_error(f"Invalid length '{plan.length}'. Must be one of: {VALID_LENGTHS}")

        # Content type validation
        if plan.content_type not in VALID_CONTENT_TYPES:
            result.add_warning(f"Uncommon content type '{plan.content_type}'")

        # Strategy validation
        if plan.strategy not in VALID_STRATEGIES:
            result.add_warning(f"Uncommon strategy '{plan.strategy}'")

        # CTA validation
        if plan.cta not in VALID_CTAS:
            result.add_warning(f"Uncommon CTA '{plan.cta}'")

        # Emoji level
        if plan.emoji_level not in VALID_EMOJI_LEVELS:
            result.add_warning(f"Uncommon emoji level '{plan.emoji_level}'")

        # Goal-audience consistency
        if plan.goal == "promote" and plan.audience == "students":
            result.add_warning("Promotional content for students may have low engagement")

        # Length-content type consistency
        if plan.content_type == "story" and plan.length == "long":
            result.add_warning("Stories are typically short — consider 'short' length")

        # Platform-content type consistency
        if plan.platform == "linkedin" and plan.content_type in ("reel", "story"):
            result.add_warning(f"'{plan.content_type}' is not optimal for LinkedIn")

        # Custom rules
        for rule in self._custom_rules:
            rule_result = rule(plan)
            if rule_result:
                if rule_result.get("error"):
                    result.add_error(rule_result["error"])
                elif rule_result.get("warning"):
                    result.add_warning(rule_result["warning"])

        return result

    def add_rule(self, rule_fn: Any) -> None:
        """Add a custom validation rule function."""
        self._custom_rules.append(rule_fn)

    def quick_check(self, plan: WritingPlan) -> bool:
        """Quick validity check without full validation."""
        return bool(plan.topic and plan.goal in VALID_GOALS and plan.platform in VALID_PLATFORMS)
