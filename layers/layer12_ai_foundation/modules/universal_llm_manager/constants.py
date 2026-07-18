"""Constants for LLM Manager."""
from __future__ import annotations

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TIMEOUT = 60.0
MAX_RETRIES = 3
RETRY_DELAY = 1.0
CACHE_TTL = 300
MAX_CONCURRENT_REQUESTS = 10

SUPPORTED_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "claude": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
    "gemini": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "mistral": ["mistral-large-latest", "mistral-medium-latest"],
    "cohere": ["command-r-plus", "command-r"],
    "grok": ["grok-3", "grok-2"],
    "ollama": ["llama3.1", "mistral", "codellama"],
}

MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
}
