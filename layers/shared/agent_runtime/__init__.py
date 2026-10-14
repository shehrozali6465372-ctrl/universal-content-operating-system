"""Shared UCOS agent runtime contracts and implemented specialist agents."""
from .contracts import (
    AgentEvidence, AgentManifest, AgentResult, AgentRole, AgentRunStatus, AgentScope, AgentTask,
)
from .registry import AgentRegistry, AgentRegistryError
from .super_intelligence import SuperIntelligenceAgent, GoalPlanError
from .research_agent import ResearchAgent, RESEARCH_AGENT_VERSION, RESEARCH_CAPABILITIES

__all__ = [
    "AgentEvidence", "AgentManifest", "AgentResult", "AgentRegistry",
    "AgentRegistryError", "AgentRole", "AgentRunStatus", "AgentScope", "AgentTask",
    "SuperIntelligenceAgent", "GoalPlanError",
    "ResearchAgent", "RESEARCH_AGENT_VERSION", "RESEARCH_CAPABILITIES",
]
