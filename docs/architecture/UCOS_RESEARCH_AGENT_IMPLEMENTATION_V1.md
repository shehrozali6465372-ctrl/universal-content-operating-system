# UCOS Research Agent — implementation contract v1.0

**Owner:** CEO / Super Intelligence Agent  
**Specialist:** Research Agent (AgentRole.RESEARCH)  
**Existing implementation owner:** Layer 02 — Research Engine  
**Status:** Implementation slice pushed for CI; production certification still requires real source-adapter wiring and deployment evidence.

## One agent, existing Layer 02 capabilities

~~~~mermaid
flowchart TD
    CEO["CEO / Super Intelligence"] --> TASK["Scoped research task"]
    TASK --> AGENT["Research Agent (single entry point)"]
    AGENT --> PLAN["Layer 02 Research Planner"]
    PLAN --> ORCH["Layer 02 Research Orchestrator"]
    ORCH --> TREND["Trend Discovery"]
    ORCH --> TOPIC["Topic Intelligence"]
    ORCH --> COMP["Competitor Analysis"]
    ORCH --> AUD["Audience Research"]
    ORCH --> KNOW["Knowledge Collector"]
    ORCH --> FACT["Fact Verification"]
    ORCH --> MEM["Research Memory"]
    ORCH --> SCORE["Topic Scoring"]
    TREND --> RESULT["Structured module results + source URLs"]
    TOPIC --> RESULT
    COMP --> RESULT
    AUD --> RESULT
    KNOW --> RESULT
    FACT --> RESULT
    MEM --> RESULT
    SCORE --> RESULT
    RESULT --> VERIFY["Research Agent validates provenance"]
    VERIFY --> CEO
~~~~

This is one logical Research Agent using existing Layer 02 modules, not eight new agents and not a second research engine. Layer 02 remains the domain-capability owner; the agent owns CEO-facing delegation, scope propagation, status, evidence validation and result formatting.

## Execution contract

- The agent accepts only the research role and one of its declared research capabilities.
- Every task carries the CEO-assigned tenant/workspace/brand scope. User input cannot override those values.
- All eight modules in the Layer 02 default workflow must be bound to concrete callable implementations. Missing or unused bindings fail at construction; no simulated provider or placeholder module is substituted.
- The existing Layer 02 planner creates a research plan; the existing orchestrator runs its dependency-aware workflow.
- Module outputs are returned in a JSON-safe form so findings and citation fields are available to the agent.
- A module with no explicit confidence receives 0.0, not a fabricated confidence score.
- A task is completed only when the workflow completes and outputs include well-formed HTTP(S) source references. Missing provenance yields partial status; URL syntax alone is not proof that a source is reachable or accurate. Execution errors are surfaced.
- A layer02://research/... reference is an internal execution trace, never represented as an external source URL.

## Boundaries and cleanup

- Do not delete the 23 logical layers or Layer 02 modules: these are the existing capability implementations being reused by the Research Agent.
- Do not add one deployment service per agent.
- Do not mark an adapter production-ready until its real search/source-provider binding, durable storage path, and live evidence are verified.
- The Research Agent is the only specialist implemented in this slice. Other specialist roles remain unimplemented pending separate scoped work.

## Verification

Focused CI tests cover module-binding completeness, Layer 02 planner/orchestrator execution, source-provenance gating, failure propagation, scope isolation, and CEO delegation/persistence. Green unit tests alone do not certify live provider integration or production deployment.
