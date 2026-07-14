"""
Task Decomposer
Layer 2: Research Engine — Module 9

Decomposes research goals into executable tasks:
- Goal-based decomposition
- Template-based task generation
- Module-specific tasks
"""

from typing import Dict, List, Optional
from layers.layer02_research.modules.research_planner.research_plan import PlanTask


# Task templates for each research module
MODULE_TASKS: Dict[str, List[Dict]] = {
    "trend_discovery": [
        {"name": "Discover trending topics", "module": "trend_discovery", "priority": "HIGH",
         "estimated_time_min": 3.0, "estimated_api_calls": 2},
        {"name": "Score and filter trends", "module": "trend_discovery", "priority": "MEDIUM",
         "estimated_time_min": 2.0},
    ],
    "topic_intelligence": [
        {"name": "Analyze topic scoring", "module": "topic_intelligence", "priority": "HIGH",
         "estimated_time_min": 3.0},
        {"name": "Cluster related topics", "module": "topic_intelligence", "priority": "MEDIUM",
         "estimated_time_min": 2.0},
    ],
    "competitor_analysis": [
        {"name": "Analyze competitor profiles", "module": "competitor_analysis", "priority": "HIGH",
         "estimated_time_min": 5.0, "estimated_api_calls": 3},
        {"name": "Detect content gaps", "module": "competitor_analysis", "priority": "MEDIUM",
         "estimated_time_min": 3.0},
        {"name": "Find opportunities", "module": "competitor_analysis", "priority": "MEDIUM",
         "estimated_time_min": 2.0},
    ],
    "audience_research": [
        {"name": "Profile audience segments", "module": "audience_research", "priority": "HIGH",
         "estimated_time_min": 4.0},
        {"name": "Map audience interests", "module": "audience_research", "priority": "MEDIUM",
         "estimated_time_min": 3.0},
        {"name": "Predict engagement", "module": "audience_research", "priority": "MEDIUM",
         "estimated_time_min": 2.0},
    ],
    "knowledge_collector": [
        {"name": "Collect knowledge from sources", "module": "knowledge_collector", "priority": "HIGH",
         "estimated_time_min": 5.0, "estimated_api_calls": 5},
        {"name": "Clean and deduplicate content", "module": "knowledge_collector", "priority": "MEDIUM",
         "estimated_time_min": 2.0},
    ],
    "fact_verification": [
        {"name": "Extract claims from content", "module": "fact_verification", "priority": "CRITICAL",
         "estimated_time_min": 3.0},
        {"name": "Verify claims against evidence", "module": "fact_verification", "priority": "CRITICAL",
         "estimated_time_min": 5.0, "estimated_api_calls": 3},
        {"name": "Detect contradictions", "module": "fact_verification", "priority": "HIGH",
         "estimated_time_min": 2.0},
    ],
    "research_memory": [
        {"name": "Store research findings", "module": "research_memory", "priority": "MEDIUM",
         "estimated_time_min": 2.0},
        {"name": "Update knowledge graph", "module": "research_memory", "priority": "LOW",
         "estimated_time_min": 2.0},
    ],
    "topic_scoring": [
        {"name": "Score topic overall", "module": "topic_scoring", "priority": "HIGH",
         "estimated_time_min": 2.0},
        {"name": "Generate recommendation", "module": "topic_scoring", "priority": "HIGH",
         "estimated_time_min": 1.0},
    ],
}


class TaskDecomposer:
    """Decompose research goals into tasks."""

    def __init__(self):
        self._templates = dict(MODULE_TASKS)

    def decompose(
        self,
        topic: str,
        modules: Optional[List[str]] = None,
        custom_tasks: Optional[List[Dict]] = None,
    ) -> List[PlanTask]:
        """Decompose a topic into research tasks."""
        if modules is None:
            modules = list(self._templates.keys())

        tasks = []
        for module in modules:
            template_tasks = self._templates.get(module, [])
            for t in template_tasks:
                task = PlanTask(
                    name=f"{t['name']} for '{topic}'",
                    description=t.get("description", ""),
                    module=module,
                    priority=t.get("priority", "MEDIUM"),
                    estimated_time_min=t.get("estimated_time_min", 5.0),
                    estimated_api_calls=t.get("estimated_api_calls", 0),
                    estimated_memory_mb=t.get("estimated_memory_mb", 10.0),
                )
                tasks.append(task)

        # Add custom tasks
        for ct in (custom_tasks or []):
            task = PlanTask(
                name=ct.get("name", "Custom task"),
                description=ct.get("description", ""),
                module=ct.get("module", "custom"),
                priority=ct.get("priority", "MEDIUM"),
                estimated_time_min=ct.get("estimated_time_min", 5.0),
            )
            tasks.append(task)

        return tasks

    def decompose_minimal(self, topic: str) -> List[PlanTask]:
        """Minimal decomposition: one key task per critical module."""
        critical = ["trend_discovery", "knowledge_collector", "fact_verification", "topic_scoring"]
        return self.decompose(topic, modules=critical)

    def add_template(self, module: str, tasks: List[Dict]):
        """Add or update task templates for a module."""
        self._templates[module] = tasks

    def get_modules(self) -> List[str]:
        return list(self._templates.keys())
