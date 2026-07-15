"""Goal Analyzer — Analyze and refine content goals from intelligence input."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


GOAL_TYPES = {
    "educate": {"keywords": ["how", "guide", "learn", "explain", "tutorial", "tips"],
                "cta_options": ["engage", "comment", "share"], "tone_range": ["friendly", "informative", "professional"]},
    "entertain": {"keywords": ["funny", "meme", "story", "viral", "amazing", "shocking"],
                  "cta_options": ["share", "engage", "comment"], "tone_range": ["humorous", "casual", "playful"]},
    "inspire": {"keywords": ["motivation", "success", "journey", "overcome", "believe", "dream"],
                "cta_options": ["share", "engage", "comment"], "tone_range": ["inspiring", "emotional", "friendly"]},
    "promote": {"keywords": ["product", "service", "offer", "launch", "discount", "buy"],
                "cta_options": ["visit", "subscribe", "share"], "tone_range": ["professional", "enthusiastic", "friendly"]},
    "engage": {"keywords": ["poll", "question", "debate", "opinion", "what", "agree"],
               "cta_options": ["comment", "share", "engage"], "tone_range": ["casual", "conversational", "playful"]},
}


class GoalAnalysis:
    """Result of goal analysis."""
    __slots__ = ("primary_goal", "secondary_goals", "confidence", "reasons",
                 "suggested_cta", "suggested_tone", "content_direction")

    def __init__(self) -> None:
        self.primary_goal = "educate"
        self.secondary_goals: List[str] = []
        self.confidence = 0.5
        self.reasons: List[str] = []
        self.suggested_cta = "engage"
        self.suggested_tone = "friendly"
        self.content_direction = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_goal": self.primary_goal,
            "secondary_goals": self.secondary_goals,
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
            "suggested_cta": self.suggested_cta,
            "suggested_tone": self.suggested_tone,
            "content_direction": self.content_direction,
        }


class GoalAnalyzer:
    """Analyzes intelligence inputs to determine content goals."""

    def __init__(self) -> None:
        self._goal_history: List[str] = []

    def analyze(
        self,
        topic: str,
        intelligence_data: Optional[Dict[str, Any]] = None,
        user_goal: Optional[str] = None,
    ) -> GoalAnalysis:
        """Analyze topic and intelligence to determine content goal."""
        result = GoalAnalysis()

        if user_goal and user_goal in GOAL_TYPES:
            result.primary_goal = user_goal
            result.confidence = 0.9
            result.reasons.append(f"User specified goal: {user_goal}")
        else:
            detected = self._detect_goal(topic, intelligence_data)
            result.primary_goal = detected["goal"]
            result.confidence = detected["confidence"]
            result.reasons = detected["reasons"]

        # Secondary goals
        result.secondary_goals = self._find_secondary(result.primary_goal, topic)

        # CTA
        goal_config = GOAL_TYPES.get(result.primary_goal, GOAL_TYPES["educate"])
        result.suggested_cta = goal_config["cta_options"][0]

        # Tone
        result.suggested_tone = goal_config["tone_range"][0]

        # Direction
        result.content_direction = self._build_direction(result, topic)

        self._goal_history.append(result.primary_goal)
        return result

    def _detect_goal(self, topic: str, intel: Optional[Dict]) -> Dict[str, Any]:
        topic_lower = topic.lower()
        scores: Dict[str, float] = {}

        for goal_name, config in GOAL_TYPES.items():
            score = 0.0
            reasons: List[str] = []
            for kw in config["keywords"]:
                if kw in topic_lower:
                    score += 0.15
                    reasons.append(f"Keyword '{kw}' matched")
            if intel:
                intent = intel.get("intent", "")
                if intent == goal_name:
                    score += 0.3
                    reasons.append(f"Intelligence intent matches '{goal_name}'")
            scores[goal_name] = score

        best = max(scores, key=scores.get) if scores else "educate"
        best_score = scores.get(best, 0.0)
        confidence = min(best_score + 0.3, 1.0)

        reasons = [f"Topic analysis suggests '{best}' goal"]
        if best_score == 0:
            reasons = ["No strong signal detected, defaulting to 'educate'"]
            confidence = 0.4

        return {"goal": best, "confidence": confidence, "reasons": reasons}

    def _find_secondary(self, primary: str, topic: str) -> List[str]:
        secondary: List[str] = []
        if primary == "educate":
            secondary = ["engage"]
        elif primary == "entertain":
            secondary = ["engage"]
        elif primary == "inspire":
            secondary = ["educate"]
        elif primary == "promote":
            secondary = ["educate", "engage"]
        elif primary == "engage":
            secondary = ["educate"]
        return secondary

    def _build_direction(self, analysis: GoalAnalysis, topic: str) -> str:
        return f"Create {analysis.primary_goal} content about '{topic}' targeting {analysis.suggested_cta}"

    @property
    def goal_history(self) -> List[str]:
        return list(self._goal_history)
