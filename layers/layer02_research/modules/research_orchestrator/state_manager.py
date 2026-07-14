"""
State Manager
Layer 2: Research Engine — Module 10

Manages state transitions for the research workflow:
- Valid transition enforcement
- Transition history
- State queries
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from layers.layer02_research.modules.research_orchestrator.exceptions import StateError


# Allowed transitions: from_state -> set of valid to_states
VALID_TRANSITIONS: Dict[str, Set[str]] = {
    "created":   {"planned", "cancelled"},
    "planned":   {"running", "cancelled"},
    "running":   {"paused", "completed", "failed", "cancelled"},
    "paused":    {"resuming", "cancelled"},
    "resuming":  {"running", "cancelled"},
    "retrying":  {"running", "failed", "cancelled"},
    "failed":    {"retrying", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


class StateManager:
    """Enforces valid state transitions and tracks history."""

    def __init__(self):
        self._history: List[Dict] = []

    def can_transition(self, from_state: str, to_state: str) -> bool:
        """Check if a transition is valid."""
        allowed = VALID_TRANSITIONS.get(from_state, set())
        return to_state in allowed

    def transition(self, current_state: str, new_state: str, reason: str = "") -> str:
        """Perform a state transition. Returns the new state."""
        if not self.can_transition(current_state, new_state):
            raise StateError(
                f"Invalid transition: {current_state} -> {new_state}. "
                f"Allowed: {VALID_TRANSITIONS.get(current_state, set())}"
            )

        self._history.append({
            "from": current_state,
            "to": new_state,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return new_state

    def get_history(self) -> List[Dict]:
        """Get full transition history."""
        return list(self._history)

    def get_last_transition(self) -> Optional[Dict]:
        """Get the most recent transition."""
        return self._history[-1] if self._history else None

    def is_terminal(self, state: str) -> bool:
        """Check if a state is terminal (no further transitions)."""
        return state in ("completed", "cancelled")

    def is_active(self, state: str) -> bool:
        """Check if the workflow is in an active state."""
        return state in ("running", "paused", "resuming", "retrying")

    def reset(self):
        """Clear transition history."""
        self._history.clear()
