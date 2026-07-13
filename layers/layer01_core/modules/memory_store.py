"""
Memory Store Definitions
Layer 1: Core System — Module 5

Defines the 4 memory levels and their metadata.
Each level has its own storage characteristics.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum


class MemoryLevel(str, Enum):
    STM = "short_term"        # Current task/conversation/session
    WORKING = "working"       # Active goals, plans, decisions
    LTM = "long_term"         # Brand voice, patterns, strategies
    EPISODIC = "episodic"     # History, mistakes, improvements


@dataclass
class MemoryLevelConfig:
    """Configuration for a memory level."""
    level: MemoryLevel
    description: str
    max_entries: int          # Max entries before compression/eviction
    auto_compress: bool       # Auto-compress when full
    persistent: bool          # Survive restarts (stored in DB)
    searchable: bool          # Included in search operations
    tags: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# MEMORY LEVEL CONFIGURATIONS
# ──────────────────────────────────────────────

STM_CONFIG = MemoryLevelConfig(
    level=MemoryLevel.STM,
    description="Short-Term: Current task, conversation, session context",
    max_entries=100,
    auto_compress=True,
    persistent=False,      # Lost on restart (RAM-like)
    searchable=True,
    tags=["task", "conversation", "session"],
)

WORKING_CONFIG = MemoryLevelConfig(
    level=MemoryLevel.WORKING,
    description="Working: Active goals, plans, decisions, current context",
    max_entries=50,
    auto_compress=False,
    persistent=True,       # Saved to DB
    searchable=True,
    tags=["goal", "plan", "decision", "active"],
)

LTM_CONFIG = MemoryLevelConfig(
    level=MemoryLevel.LTM,
    description="Long-Term: Brand voice, writing style, patterns, strategies",
    max_entries=10000,
    auto_compress=True,
    persistent=True,
    searchable=True,
    tags=["brand", "style", "pattern", "strategy", "knowledge"],
)

EPISODIC_CONFIG = MemoryLevelConfig(
    level=MemoryLevel.EPISODIC,
    description="Episodic: Post history, mistakes, improvements, version history",
    max_entries=50000,
    auto_compress=True,
    persistent=True,
    searchable=True,
    tags=["history", "mistake", "improvement", "version"],
)


# ──────────────────────────────────────────────
# REGISTRY
# ──────────────────────────────────────────────

MEMORY_LEVELS: Dict[MemoryLevel, MemoryLevelConfig] = {
    MemoryLevel.STM: STM_CONFIG,
    MemoryLevel.WORKING: WORKING_CONFIG,
    MemoryLevel.LTM: LTM_CONFIG,
    MemoryLevel.EPISODIC: EPISODIC_CONFIG,
}


def get_level_config(level: MemoryLevel) -> MemoryLevelConfig:
    return MEMORY_LEVELS[level]


def get_all_levels() -> List[MemoryLevel]:
    return list(MEMORY_LEVELS.keys())


def get_persistent_levels() -> List[MemoryLevel]:
    return [lv for lv, cfg in MEMORY_LEVELS.items() if cfg.persistent]
