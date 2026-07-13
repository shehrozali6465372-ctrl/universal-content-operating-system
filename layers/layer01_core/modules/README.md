# 📦 Config Manager Module

## 🎯 Purpose
Central configuration management for the entire AI Agent. All settings controlled from one place.

## 📁 Files

| File | Purpose |
|------|---------|
| `config_manager.py` | Main config loading, access, save |
| `config_schema.py` | Required & optional setting definitions |
| `validators.py` | Value validation rules |
| `exceptions.py` | Custom error classes |

## 🚀 Usage

```python
from layers.layer01_core.modules.config_manager import ConfigManager

# Initialize
config = ConfigManager()
config.load()

# Access values
api_key = config.get("OPENAI_API_KEY")
log_level = config.get("LOG_LEVEL", default="INFO")

# Runtime update
config.set("AI_TEMPERATURE", 0.8)

# Validate all config
errors = config.validate()
if errors:
    print("Config errors:", errors)

# Save config
config.save("config/agent_config.json")
```

## ⚙️ Configuration Sources (Priority: Low → High)
1. `config/default.yaml` — Base defaults
2. `.env` file — Local overrides
3. `AGENT_*` environment variables — Highest priority

## 📋 Required Settings

| Key | Description |
|-----|-------------|
| `OPENAI_API_KEY` | OpenAI API key (sk-...) |
| `FACEBOOK_PAGE_ID` | Facebook Page ID |
| `FACEBOOK_ACCESS_TOKEN` | Facebook Graph API token |

## 🔧 Optional Settings (with defaults)

| Key | Default | Description |
|-----|---------|-------------|
| `LOG_LEVEL` | `INFO` | DEBUG/INFO/WARNING/ERROR |
| `DATABASE_PATH` | `data/agent.db` | SQLite path |
| `DEBUG` | `false` | Debug mode |
| `MAX_POSTS_PER_DAY` | `5` | Daily post limit |
| `AI_MODEL` | `gpt-4` | AI model name |
| `AI_TEMPERATURE` | `0.7` | AI creativity (0.0-1.0) |

## ❌ Errors

| Error | Meaning |
|-------|---------|
| `ConfigNotFound` | .env or config file missing |
| `InvalidConfig` | Value doesn't match rules |
| `MissingAPIKey` | Required API key not provided |
| `SchemaError` | Multiple validation failures |

## 🧪 Tests
```bash
python -m pytest layers/layer01_core/tests/test_config_manager.py -v
```
