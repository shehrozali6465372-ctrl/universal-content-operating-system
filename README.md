# 🤖 Universal AI Content Operating System

**v5.5.0** — An autonomous, platform-agnostic AI content creation and publishing system.

## Architecture

```
Layer 22 — Documentation
Layer 21 — Deployment
Layer 20 — Image Pipeline
Layer 19 — Analytics Engine
Layer 18 — Monitoring
Layer 17 — Security
Layer 16 — Database Engineering
Layer 15 — Async Runtime Engine
Layer 14 — Enterprise Integration
Layer 13 — Persistence
Layer 12 — AI Foundation (Model Router, Key Manager, Gemini)
Layer 11 — Async Runtime
Layer 10 — Monetization
Layer 9  — Self-Learning
Layer 8  — Analytics
Layer 7  — Publishing
Layer 6  — Quality & Safety
Layer 5  — Image Intelligence
Layer 4  — Content Writing
Layer 3  — AI Intelligence
Layer 2  — Research & Scraping
Layer 1  — Core System
```

## Quick Start

```bash
# Boot the system
python main.py

# Check status
python main.py --status

# Generate content (requires GEMINI_API_KEY_*)
python main.py --generate "artificial intelligence trends"
```

## API Keys

Set these environment variables (or GitHub Secrets):

```bash
export GEMINI_API_KEY_1="AIzaSy..."  # Primary
export GEMINI_API_KEY_2="AIzaSy..."  # Secondary
export GEMINI_API_KEY_3="AIzaSy..."  # Backup
```

Keys are health-tracked with automatic rotation, rate-limit detection, and failover.

## Project Scale

| Metric | Value |
|--------|-------|
| Layers | 22 |
| Python Files | 1,780+ |
| Lines of Code | 150,000+ |
| Tests | 6,989 passing |
| Git Commits | 127+ |

## Key Features

- **22-Layer Architecture** — Clean separation, zero circular dependencies
- **Intelligent Key Rotation** — 3 API keys with health tracking, cooldown, failover
- **Model Router** — Provider-agnostic (Gemini, OpenAI, Claude, DeepSeek)
- **Real Gemini API** — Actual HTTP calls via stdlib urllib
- **Prompt Builder** — Self-improving, style-aware prompt generation
- **Security** — JWT, encryption, input validation, firewall, RBAC
- **Monitoring** — Metrics, profiler, tracer, health checks, alerts
- **Database** — Repository pattern, ORM, migrations, cache, connection pool
- **Async Runtime** — Coroutine manager, worker pool, task queues, retry engine
- **Deployment** — Docker, environment manager, release manager, build pipeline

## Testing

```bash
# Full suite
python -m pytest tests/ --ignore=tests/test_core.py -q

# Specific layer
python -m pytest tests/test_phase1_integration_engine.py -v
```

## Development

```bash
# Lint
ruff check layers/ --select E,F,W --ignore E501,E402

# Version
cat VERSION
```

## Platform Support

Universal — works with any social media platform through plugin architecture:
Facebook, Instagram, X (Twitter), LinkedIn, YouTube, TikTok, Threads, Reddit, Medium, WordPress, Telegram, Discord, Binance Square, Pinterest, and future plugins.
