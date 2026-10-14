"""Shared retrieval semantics for the specialized AI memory stores."""
import pytest

from layers.layer13_persistence.modules.ai_memory_persistence.analytics_memory_store import AnalyticsMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.brand_memory_store import BrandMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.business_memory_store import BusinessMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.context_memory_store import ContextMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.conversation_memory_store import ConversationMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.goal_memory_store import GoalMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.knowledge_memory_store import KnowledgeMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.learning_memory_store import LearningMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.prompt_memory_store import PromptMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.research_memory_store import ResearchMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.semantic_memory_store import SemanticMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.strategy_memory_store import StrategyMemoryStore


@pytest.mark.parametrize(
    "store_cls",
    [
        AnalyticsMemoryStore,
        BrandMemoryStore,
        BusinessMemoryStore,
        ContextMemoryStore,
        ConversationMemoryStore,
        GoalMemoryStore,
        KnowledgeMemoryStore,
        LearningMemoryStore,
        PromptMemoryStore,
        ResearchMemoryStore,
        SemanticMemoryStore,
        StrategyMemoryStore,
    ],
)
def test_shared_retrieve_increments_access_count(store_cls):
    store = store_cls()
    entry = store.store("shared-key", "stored-value")
    assert entry.access_count == 0
    assert store.retrieve("shared-key") is entry
    assert entry.access_count == 1
