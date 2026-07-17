# 📋 Changelog

## [v0.9.0] - 2026-07-17
### Added
- **Layer 8: Analytics Engine** — Complete analytics platform with 10 modules:
  - **Data Collector** — Collect data from multiple sources, manual + auto-fetch
  - **Metric Engine** — Calculate sum/avg/median/std_dev/p95/p99/growth_rate
  - **Report Generator** — Summary and comparison reports with sections and charts
  - **Performance Analyzer** — Analyze across dimensions with benchmarks
  - **Trend Detector** — Detect UP/DOWN/STABLE trends with anomaly detection (z-score)
  - **A/B Test Engine** — Create, run, analyze A/B tests with statistical significance
  - **Funnel Analyzer** — Analyze conversion funnels, identify drop-off points
  - **Attribution Engine** — Attribute conversions (first/last/linear/weighted touch models)
  - **Dashboard Service** — Dashboard layouts, widgets, snapshots
  - **Analytics Orchestrator** — Full pipeline: collect → calculate → detect → report → dashboard
- **82 comprehensive tests** covering all 10 modules

### Stats
- Total Tests: 2736 (all passing)
- Lint: clean
- Layer 8: Complete

## [v0.8.0] - 2026-07-17
### Added
- **Layer 7 Module 10: Publishing Orchestrator** — Final coordination layer with 10 sub-modules:
  - **PipelineStage** — Define pipeline stages with order, required flag, and handlers
  - **PipelineContext** — Shared context passed through all pipeline stages
  - **PipelineExecutor** — Execute stages in order with error handling and early stop
  - **PipelineMonitor** — Track pipeline execution health (success rate, avg duration)
  - **ParallelExecutor** — Execute independent tasks in parallel with error isolation
  - **EventHandler** — Event bus integration (subscribe/publish pipeline events)
  - **ModuleRegistry** — Register and discover all 10 Layer 7 modules
  - **HealthChecker** — Monitor pipeline component health status
  - **MetricsCollector** — Collect pipeline execution metrics (success rate, error rate)
  - **PublishingOrchestrator** — Full pipeline: validate→plan→policies→schedule→upload→publish→recover→analytics→memory
- **71 comprehensive tests** covering all 10 sub-modules
- **Layer 7 Integration Sprint Complete** — All 10 modules working together

### Stats
- Total Tests: 2654 (all passing)
- Lint: clean
- Layer 7: 10/10 Modules Complete ✅ FROZEN

### Layer 7 Module Summary
1. Publishing Planner ✅
2. Platform Plugin Manager ✅
3. Media Manager ✅
4. Scheduler & Queue ✅
5. Publisher Engine ✅
6. Failure Recovery ✅
7. Analytics Hook ✅
8. Publishing Memory ✅
9. Publishing Policies ✅
10. Publishing Orchestrator ✅

## [v0.7.8] - 2026-07-17
### Added
- **Layer 7 Module 9: Publishing Policies** — Centralized, versioned platform rules with 10 sub-modules:
  - **PlatformRules** — Rule database for all platforms (FB/IG/X/LI/YT/TikTok)
  - **ContentLimits** — Platform-specific text length, image count, hashtag limits
  - **RateLimiter** — API rate limit enforcement (requests/minute, posts/day)
  - **MediaPolicies** — Image/video format, size, aspect ratio rules per platform
  - **SchedulePolicies** — Scheduling restrictions, business hours, timezone rules
  - **ContentSafety** — Content safety rules (hate speech, violence, spam, misinformation)
  - **APIVersionManager** — Track and manage platform API versions and deprecation
  - **BrandSafety** — Brand-specific blocked topics, competitor mentions, disclaimers
  - **PolicyValidator** — Validate content against all policies in one call
  - **PolicyManager** — Full pipeline orchestration: validate → rate check → report
  - **Exceptions** — PolicyError, PolicyViolationError, PolicyNotFoundError
- **89 comprehensive tests** covering all 10 sub-modules

### Stats
- Total Tests: 2583 (all passing)
- Lint: clean
- Layer 7: 9/10 Modules Complete

## [v0.7.7] - 2026-07-17
### Added
- **Layer 7 Module 8: Publishing Memory** — The publishing layer's brain with 10 sub-modules:
  - **PublishHistory** — Record all published posts with platform, time, result, tags
  - **PlatformMemory** — Track platform-specific behaviour, success rates, best content types
  - **ScheduleMemory** — Learn best posting hours, weekdays, seasonal patterns
  - **AudienceMemory** — Engagement history, audience preferences, content performance
  - **PerformanceMemory** — Reach, CTR, conversion, ROI history with platform comparison
  - **PublishFailureMemory** — Publishing failures, recovery effectiveness, error frequency
  - **PatternLearner** — Detect recurring patterns (platform, content type, time, tags)
  - **MemorySearch** — Flexible search by platform, content type, tags, text, date
  - **MemoryRetention** — Archive, cleanup, compression, expiration policy
  - **PublishingMemoryManager** — Full pipeline: store → learn → search → recommend → feed Layer 9
  - **Exceptions** — MemoryError, StorageError, SearchError
- **87 comprehensive tests** covering all 10 sub-modules

### Stats
- Total Tests: 2494 (all passing)
- Lint: clean
- Layer 7: 8/10 Modules Complete

## [v0.7.6] - 2026-07-16
### Added
- **Layer 7 Module 7: Analytics Hook** — Collect, normalize, analyze, and store publish analytics with 10 sub-modules:
  - **AnalyticsEvent** — Unified analytics event model with merge support
  - **MetricsCollector** — Fetch analytics from plugins with batch collection
  - **MetricsNormalizer** — Platform-specific → unified metric mapping (FB/IG/X/LI/YT/TikTok)
  - **EngagementAnalyzer** — Weighted engagement scoring (likes×1, comments×3, shares×5, saves×4)
  - **ReachAnalyzer** — Reach, impressions, views, frequency, completion rate
  - **ConversionTracker** — Clicks, CTR, signups, revenue, ROAS
  - **TrendTracker** — Growth trends, peak detection, viral detection
  - **AnalyticsMemory** — Historical storage, comparison, platform filtering
  - **PerformanceScorer** — Weighted scoring, letter grades (A+ → F), benchmark comparison
  - **AnalyticsManager** — Full pipeline orchestration + Layer 9 learning signals
  - **Exceptions** — AnalyticsError, FetchError, NormalizationError
- **83 comprehensive tests** covering all 10 sub-modules

### Stats
- Total Tests: 2407 (all passing)
- Lint: clean
- Layer 7: 7/10 Modules Complete

## [v0.7.5] - 2026-07-16
### Added
- **Layer 7 Module 6: Failure Recovery Engine** — Self-healing publishing pipeline with 10 sub-modules:
  - **FailureDetector** — Detect network/API/auth/rate-limit/media/content errors with severity
  - **ErrorClassifier** — Classify errors as retryable/permanent/user_action/platform_specific
  - **RetryStrategy** — Configurable retry policies (eager/normal/patient/rate_limit) with backoff
  - **CircuitBreaker** — Open/half-open/closed states to prevent API flooding
  - **RollbackManager** — Undo partial publishes and clean up resources
  - **RecoveryActions** — Recovery step factory (refresh token, re-upload, switch endpoint, delay)
  - **IncidentLogger** — Error history with context, timeline, and resolution tracking
  - **RecoveryMetrics** — Recovery success rate, retry count, MTTR, failure statistics
  - **FailureMemory** — Remember recurring failures, platform patterns, best recovery strategies
  - **RecoveryManager** — Full pipeline orchestration: detect → classify → recover → retry/rollback
  - **Exceptions** — RecoveryError, CircuitOpenError, RecoveryExhaustedError, RollbackFailedError
- **115 comprehensive tests** covering all 10 sub-modules

### Stats
- Total Tests: 2324 (all passing)
- Lint: clean
- Layer 7: 6/10 Modules Complete

## [v0.7.4] - 2026-07-16
### Added
- **Layer 7 Module 5: Publisher Engine** — Transactional, platform-agnostic publishing with 10 sub-modules:
  - **PublishRequest** — Validated request model with media, scheduling, idempotency
  - **PublishExecutor** — Execute publish, edit, delete, reschedule via plugins
  - **UploadCoordinator** — Media upload with progress tracking and validation
  - **ResponseParser** — Normalize API responses, classify errors, detect retryable
  - **StatusTracker** — Lifecycle tracking (pending → uploading → publishing → published)
  - **PublishTransaction** — Atomic execution with rollback support
  - **PublishAudit** — Full audit trail with success rate and stats
  - **PublisherResult** — Extended result model with error classification
  - **PublisherMetrics** — Success rate, API latency, upload stats, snapshots
  - **PublisherManager** — Full pipeline orchestration (validate → upload → publish → parse → audit)
  - **Exceptions** — PublishError, PublishValidationError, PublishExecutionError, UploadError, RollbackError
- **94 comprehensive tests** covering all 10 sub-modules

### Stats
- Total Tests: 2209 (all passing)
- Lint: clean
- Layer 7: 5/10 Modules Complete

## [v0.7.3] - 2026-07-16
### Added
- **Layer 7 Module 4: Scheduler & Queue** — Publishing execution system with 10 sub-modules:
  - **PublishJob** — Priority-based job model (critical/high/normal/low/background)
  - **JobQueue** — Priority queue with batch enqueue, platform filtering, peek
  - **RetryManager** — Exponential backoff with configurable retry policy
  - **DeadLetterQueue** — Failed job storage with recovery support
  - **TimezoneManager** — UTC conversion, business hours, multi-timezone support
  - **BatchPublisher** — Batch execution with platform grouping
  - **WorkerManager** — Worker pool management with load tracking
  - **QueueMetrics** — Snapshots, success rate, retry rate, history
  - **QueueOrchestrator** — Full pipeline coordination, event tracking, dead letter recovery
  - **Exceptions** — QueueError, JobNotFoundError, QueueFullError
- **114 comprehensive tests** covering all 10 sub-modules

### Stats
- Total Tests: 2115 (all passing)
- Lint: clean
- Layer 7: 4/10 Modules Complete









## [v0.5.1] - 2026-07-16
### Added
- **Layer 5 Module 11: Accessibility Engine** — Alt text generation, WCAG contrast validation, text density checks
- **Layer 5 Module 12: Visual Quality Scorer** — Composition, text density, safe margins, clickability scoring with grades
- **Layer 5 Module 13: Prompt Evaluator** — Prompt clarity/specificity/style scoring with auto-refinement
- **120+ comprehensive tests** covering all 13 modules:
  - All 8 platform image specs verified
  - All 10 prompt styles tested
  - Accessibility: contrast, alt text, text density
  - Quality: composition, clickability, grades
  - Prompt: clarity, specificity, refinement
  - Orchestrator: all platforms, types, styles
### Stats
- Total Tests: 1462 (all passing)
- Lint: clean
- Layer 5: 13/13 Modules Complete ✅ (hardened)

## [v0.5.0] - 2026-07-16
### Added
- **Layer 5 Module 1: Image Planner** — Platform-agnostic image planning (8 platforms, 10 image types)
- **Layer 5 Module 2: Image Prompt Builder** — AI image generation prompts (10 style presets)
- **Layer 5 Module 3: Image Provider** — BaseImageProvider ABC + MockImageProvider
- **Layer 5 Module 4: Layout Engine** — Platform-specific layout specifications (7 layouts)
- **Layer 5 Module 5: Thumbnail Engine** — Thumbnail planning for video platforms
- **Layer 5 Module 6: Carousel Planner** — Multi-slide carousel content planning
- **Layer 5 Module 7: Infographic Engine** — Data visualization planning (7 chart types)
- **Layer 5 Module 8: Image Optimizer** — Platform-specific optimization
- **Layer 5 Module 9: Image Memory** — Brand visual profiles + image history
- **Layer 5 Module 10: Image Orchestrator** — Plan → Prompt → Layout → Generate → Optimize → Store
- All modules platform-agnostic and independent from Writing layer
- 34 new tests across 10 test classes
### Stats
- Total Tests: 1341 (all passing)
- Lint: clean
- Layer 5: 10/10 Modules Complete ✅

## [v0.4.3] - 2026-07-15
### Added
- **Layer 1-4 Integration Sprint** — End-to-end pipeline tests
  - Topic → Research → Intelligence → Writing → Multi-platform output
  - Confidence propagation across all layers
  - Strategy goals → Writing plan → Draft generation
  - Performance timing validation
  - Memory persistence across pipeline runs
  - A/B variant generation through pipeline
  - 7 integration tests
### Stats
- Total Tests: 1307 (all passing)
- Lint: clean
- Layer 1-4: Fully integrated ✅

## [v0.4.2] - 2026-07-15
### Added
- **Layer 4 Module 3: Caption Engine** — Platform-specific caption generation (13 platforms)
- **Layer 4 Module 4: Hashtag & Keyword Engine** — Hashtags + SEO keywords (6 categories)
- **Layer 4 Module 5: Tone Adapter** — Cross-platform tone adaptation (12 tones)
- **Layer 4 Module 6: Hook Engine** — Scroll-stopping hooks (6 types with alternatives)
- **Layer 4 Module 7: CTA Engine** — Platform-specific CTAs (6 platforms, batch generation)
- **Layer 4 Module 8: Content Optimizer** — SEO, readability, platform optimization
- **Layer 4 Module 9: Writing Memory** — Brand voice consistency + draft storage
- **Layer 4 Module 10: Writing Orchestrator** — One topic → multiple optimized platform outputs
- **Universal design**: All modules platform-agnostic (Facebook, Instagram, Twitter, LinkedIn, TikTok, YouTube, Pinterest, Threads, Reddit, Medium)
- 55 new tests across 8 test classes
### Stats
- Total Tests: 1300 (all passing)
- Lint: clean
- Layer 4: 10/10 Modules Complete ✅

## [v0.4.1] - 2026-07-15
### Added
- **Layer 4 Module 2: Draft Generator** (Production-grade with LLM abstraction)
  - `llm_provider.py` — BaseLLMProvider ABC + MockLLMProvider for testing
  - `prompt_builder.py` — Build system/user prompts from WritingPlan (10 tones, 5 goals, 10 strategies)
  - `draft_validator.py` — Validate drafts for length, repetition, URLs, profanity, custom rules
  - `variant_generator.py` — A/B variant generation (original, alternative, bold, minimal, detailed, emotional, question_hook, stat_hook)
  - `draft_memory.py` — Store/retrieve past drafts with topic/plan indexing
  - `draft_manager.py` — Central orchestrator: Plan → Prompt → LLM → Validate → Store → Return
  - Full LLM abstraction: swap providers without changing business logic
  - Zero vendor lock-in: OpenAI, Gemini, Claude all supported via BaseLLMProvider
  - 43 new tests across 7 test classes
### Stats
- Total Tests: 1245 (all passing)
- Lint: clean
- Layer 4 Progress: 2/10 Modules

## [v0.4.0] - 2026-07-15
### Added
- **Layer 4 Module 1: Content Planner** (Production-grade)
  - `writing_plan.py` — Core WritingPlan data model with serialization
  - `goal_analyzer.py` — 5-goal detection (educate, entertain, inspire, promote, engage) with keyword matching
  - `audience_analyzer.py` — 7 audience profiles (students, professionals, tech, entrepreneurs, parents, creators, general)
  - `platform_planner.py` — 5 platform specs (Facebook, Instagram, Twitter, LinkedIn, YouTube) with constraints
  - `tone_selector.py` — 10 tone profiles with goal-audience-platform matching
  - `content_structure.py` — 7 structure templates (educational, entertaining, promotional, inspiring, engaging, carousel, story)
  - `constraint_manager.py` — Writing constraint system with must/should/prefer severity levels
  - `plan_validator.py` — Comprehensive validation with error/warning/scoring
  - `planner_manager.py` — Central orchestrator: goal→audience→platform→tone→structure→validate→plan
  - Zero LLM API calls — pure planning module (LLM integration in Module 2)
  - 69 new tests across 10 test classes
### Stats
- Total Tests: 1200 (all passing)
- Lint: clean
- Layer 4 Progress: 1/10 Modules

## [v0.3.16] - 2026-07-15
### Added
- **Layer 3 Integration Sprint** — End-to-end pipeline tests
  - Full pipeline: Content → Trend → Quality → Strategy → Memory
  - Confidence propagation across modules
  - Cross-module data fusion verification
  - Orchestrator batch analysis
  - Strategy memory integration
  - Performance timing validation
  - 10 integration tests across full Layer 3
### Stats
- Total Tests: 1131 (all passing)
- Lint: clean
- Layer 3: Complete & integrated ✅

## [v0.3.15] - 2026-07-15
### Added
- **Layer 3 Module 10: Intelligence Orchestrator** (Production-grade)
  - `IntelOrchestrator` — Full pipeline: content understanding → trend analysis → quality → strategy → recommendations
  - `PipelineEvent` — Per-module events tracking for observability
  - `ModuleMetrics` — Execution count, timing, success/failure rates per module
  - `HealthStatus` — Module health monitoring with degraded detection
  - Cache with metadata tracking (cached/not cached)
  - Enhanced error handling with module-level exception catching
  - `analyze_batch()` — Multi-topic analysis
  - Backward-compatible with existing API
  - 27 new tests across 5 test classes
### Stats
- Total Tests: 1121 (all passing)
- Lint: clean
- Layer 3 Progress: 10/10 Modules Complete ✅

## [v0.3.14] - 2026-07-15

### Added
- **Layer 3 Module 9: Intelligence Memory** (Production-grade, enhanced from skeleton)
  - `pattern_indexer.py` — Pattern indexing with frequency, confidence tracking, type/tag search
  - `case_retriever.py` — Similar case retrieval by topic, tag, score range, text search
  - `memory_consolidator.py` — Merge similar entries with frequency/confidence scoring
  - `memory_pruner.py` — Age and value-based pruning with analysis reports
  - `memory_versioning.py` — Version history with rollback support
  - `intelligence_store.py` — Core storage with category/tag indexes, search, CRUD
  - `confidence_history.py` — Confidence trend tracking, module averages, topic trends
  - `memory_searcher.py` — Cross-store search with relevance scoring
  - `intel_memory_manager.py` — Central orchestrator: remember, recall, learn, search, consolidate, prune
  - Fixed timestamp-based ID collisions across all sub-modules (now uses counters)
  - 58 new tests across 10 test classes
### Stats
- Total Tests: 1094 (all passing)
- Lint: clean
- Layer 3 Progress: 9/10 Modules complete

## [v0.3.13] - 2026-07-15
### Added
- **Layer 3 Module 8: Strategy Engine** (Production-grade, enhanced from skeleton)
  - `strategy_generator.py` — Dynamic strategy generation from intelligence inputs (trend, audience, competitor, content data)
  - `strategy_evaluator.py` — Multi-dimension evaluation (feasibility, impact, confidence, risk, resource efficiency, alignment)
  - `strategy_adapter.py` — Real-time adaptation based on engagement, trend, competition signals and constraints
  - `goal_planner.py` — Multi-goal planning with topological sort, dependency resolution, critical path analysis
  - `risk_analyzer.py` — 6-factor risk assessment with mitigations (competition, volatility, quality, fit, saturation, confidence)
  - `strategy_selector.py` — Weighted multi-criteria selection with constraint filtering
  - `strategy_memory.py` — Past strategy storage with outcomes, lessons, similarity search, stats
  - `strategy_explainer.py` — Human-readable strategy explanations with reasoning, risks, expected outcomes
  - `strategy_manager.py` — Central orchestrator: generate → evaluate → risk-assess → select → explain → store
  - Backward-compatible with original `StrategyEngine` API
  - 76 new tests across 9 test classes
### Stats
- Total Tests: 1036 (all passing)
- Lint: clean
- Layer 3 Progress: 8/10 Modules complete

## [v0.3.12] - 2026-07-15
### Added
- **Layer 3 Module 6: Learning Signals** (Complete)
  - `signal_collector.py` — Collect raw signals from multiple sources
  - `signal_normalizer.py` — Normalize raw signals to 0-1 scale (min-max, z-score)
  - `engagement_calculator.py` — Composite engagement scoring with configurable weights
  - `feedback_analyzer.py` — Positive/negative feedback ratio and sentiment trend
  - `performance_tracker.py` — Content performance tracking over time with snapshots
  - `signal_manager.py` — Central orchestrator combining all sub-modules with learning score
- **Layer 3 Module 7: Knowledge Fusion** (Complete)
  - `fusion_engine.py` — Unified intelligence object from multiple intelligence sources
  - `evidence_aggregator.py` — Aggregates supporting and contradicting evidence
  - `source_ranker.py` — Ranks intelligence sources by reliability, relevance, freshness
  - `intelligence_merger.py` — Merges intelligence objects with conflict detection
  - `fusion_manager.py` — Central orchestrator for Knowledge Fusion
- **test_remaining_modules.py** updated to use current APIs
- 32 new tests across 12 test classes

### Stats
- Total Tests: 960 (all passing)
- Lint: clean
- Layer 3 Progress: 7/10 Modules complete

## [v0.3.11] - 2026-07-15
### Added
- **Layer 3 Module 5: Recommendation Engine** (Complete)
  - `candidate_generator.py` — Generates candidates from trends, audience gaps, competitor, knowledge
  - `ranking_engine.py` — Weighted multi-signal ranking with configurable weights
  - `constraint_filter.py` — Custom constraint-based candidate filtering
  - `diversity_engine.py` — Ensures recommendations span multiple categories/sources
  - `novelty_engine.py` — Boosts novel/rare topics based on history
  - `explanation_builder.py` — Generate why/why_not reasons for each recommendation
  - `confidence_calculator.py` — Multi-factor confidence with risk levels
  - `recommendation_memory.py` — Stores past recommendations and outcomes
  - `feedback_collector.py` — Collects and aggregates feedback signals
  - `recommendation_manager.py` — Orchestrator: generate -> filter -> rank -> diversify -> explain
  - Each recommendation includes: score, confidence, why, why_not, alternatives
  - 19 new tests across 10 test classes

### Stats
- Total Tests: 939 (all passing)
- Layer 3 Progress: 5/10 Modules complete

## [v0.3.10] - 2026-07-15
### Added
- **Layer 3 Module 4: Content Intelligence** (Complete)
  - `quality_estimator.py` — Multi-dimension quality scoring (grammar, clarity, engagement, relevance, originality)
  - `readability_analyzer.py` — Flesch-Kincaid readability with grade level and reading time
  - `emotional_analyzer.py` — 7-emotion detection (joy, sadness, anger, fear, surprise, trust, anticipation)
  - `virality_predictor.py` — Content-level virality prediction (hook, emotion, uniqueness, shareability)
  - `audience_fit_analyzer.py` — Content-audience alignment scoring
  - `novelty_detector.py` — Content uniqueness detection with hash-based dedup
  - `redundancy_detector.py` — N-gram repetition detection
  - `hook_analyzer.py` — Opening hook type detection and scoring
  - `cta_analyzer.py` — Call-to-action detection (engagement, traffic, conversion, community)
  - `content_optimizer.py` — Automated improvement suggestions with priority
  - `content_confidence.py` — Confidence scoring for content
  - `intelligence_manager.py` — Orchestrator combining all 11 sub-modules
  - 24 new tests across 12 test classes
- **Module 3 Enhancements**
  - `decision_graph.py` — Decision dependency graph with critical path and weak link detection
  - `counterfactual_reasoner.py` — What-if analysis with impact estimation
  - `confidence_evolution.py` — Confidence through pipeline stages
  - `decision_replay.py` — Decision sequence replay
  - `multi_objective_optimizer.py` — Pareto optimization across competing objectives

### Fixed
- IntelligenceOrchestrator compatibility with updated QualityResult API

### Stats
- Total Tests: 920 (all passing)
- Layer 3 Progress: 4/10 Modules

## [v0.3.9] - 2026-07-14
### Added
- Module 3 enhancements: decision_graph, counterfactual_reasoner, confidence_evolution, decision_replay, multi_objective_optimizer
- 25 new tests for enhancements

### Stats
- Total Tests: 905

## [v0.3.8] - 2026-07-14
### Added
- Layer 3 Module 3: Reasoning Engine (Complete)
- 46 tests across 11 test classes

### Stats
- Total Tests: 880
- Layer 3 Progress: 3/10

## [v0.3.7] - 2026-07-13
### Added
- Module 2 enhancements: Trend Evidence, History, Events, Confidence Breakdown
- 22 new tests

### Stats
- Total Tests: 834

## [v0.3.6] - 2026-07-13
### Added
- Layer 3 Module 2: Trend Intelligence (Complete)
- 10 sub-modules, 25 new tests

### Stats
- Total Tests: 812

## [v0.3.5] - 2026-07-13
### Added
- Module 1 final features: Contradiction Detection, Semantic Clustering, Duplicate Detection, Batch

### Stats
- Total Tests: 780

## [v0.3.4] - 2026-07-13
### Added
- Module 1 enhancements: embeddings, hierarchy, ambiguity, confidence calibration
- 49 new tests

### Fixed
- Public API freeze for SemanticAnalyzer

### Stats
- Total Tests: 731

## [v0.3.3] - 2026-07-13
### Added
- Module 1 Sprint 2: Entity Linking, Topic Hierarchy, Explainable Confidence, Reasoning

### Stats
- Total Tests: 575

## [v0.3.2] - 2026-07-13
### Added
- Layer 3 Module 1: Semantic Analyzer Sprint 1 core
- 68 tests across 8 test classes

### Stats
- Total Tests: 400

## [v0.3.1] - 2026-07-13
### Added
- Global Event Bus
- Shared Models
- Dependency Injection Container
- Plugin System (Base, Registry)
- Layer interfaces (IResearch, IIntelligence)
- AI Provider Abstraction (BaseLLM, OpenAIProvider)
- ASGI / async pipeline support

### Stats
- Total Tests: 300+
- Layer 3 Start: building intelligence abstraction

## [v0.2.9] - 2026-07-13
### Added
- Layer 2 Module 10: Research Orchestrator (Complete)
- Layer 2: End-to-end research pipeline done:
  Trend → Topic → Competitor → Audience → Knowledge → Fact → Memory → Scoring → Planner → Orchestrator
- Layer 2 FULL COMPLETE

### Stats
- Total Tests: 1170+ (L1: 360 + L2: 807)
- Layer 2 Progress: 10/10 modules (100%)

## [v0.2.8] - 2026-07-12
### Added
- Layer 2 Module 9: Research Planner with Goal Manager, Task Decomposer,
  Dependency Graph (DAG), Priority Engine, Resource Estimator, Plan Optimizer, Planner Manager

### Stats
- Total Tests: ~1167
- Layer 2 Progress: 9/10 (90%)

## [v0.2.7] - 2026-07-12
### Added
- Layer 2 Module 8: Topic Scoring Engine (14 niche weight profiles, Bayesian fusion, opportunity/risk scores)
- 62 new tests across 8 test classes

### Stats
- Total Tests: 1021

## [v0.2.6] - 2026-07-12
### Added
- Layer 2 Module 7: Research Memory + Decision Trace Engine
- 89 new tests across 8 test classes

### Stats
- Total Tests: 959

## [v0.2.5] - 2026-07-12
### Added
- Layer 2 Module 6: Fact Verification
- Claim extract, evidence matching, source validation, contradiction detection, citations, verification pipeline
- 64 new tests

### Stats
- Total Tests: 870

## [v0.2.4] - 2026-07-12
### Added
- Layer 2 Module 5: Knowledge Collector + Global Confidence Engine (shared)
- Source registry, dedup, cache, metadata extraction
- 108 new tests (15 Confidence Engine tests)
- Total Tests: 806

## v0.2.3 — Layer 2 Module 4: Audience Research
## v0.2.2 — CI/CD, lint, coverage 95%
## v0.2.0 — Layer 2 Start
## v0.1.11 — Layer 1 Full Complete (10/10 modules, 360 tests)
...
