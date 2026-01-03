# AGENTS.md (Single Source of Truth)

> Canonical instructions now live in `docs/AGENTS.md`. This file mirrors the same guardrails for convenience; consult `docs/AGENTS.md` for the definitive, kept-in-sync version.

## Guardrail Hierarchy
- `docs/AGENTS.md` remains the canonical source; this root file mirrors it.
- Any nested `AGENTS.md` may only tighten these guardrails and must explicitly inherit from this hierarchy.

## Design Tenets
- Security-first, offline-first defaults with strict allowlists/denylists and deterministic behavior across planner, worker, coordinator, and sandboxes.
- Registry-driven control planes only; tool swaps and sandbox changes must land as `registry.yaml` diffs with deterministic ordering and audit traces.

## Agent Roles & Interfaces
- PlannerAgent accepts `(goal: str, metadata: dict)` and returns ordered steps with streaming-friendly traces.
- WorkerAgent executes ordered steps against allowlisted tools and enforces tool schemas; CoordinatorAgent preserves trace ordering with thread-safe round-robin worker selection.
- **OrchestratorProtocol** (Canonical): All orchestration logic MUST implement `cuga.orchestrator.OrchestratorProtocol` defining lifecycle stages (initialize/plan/route/execute/aggregate/complete), explicit routing decisions, structured error propagation with failure modes, and immutable execution context with trace_id continuity. See `docs/orchestrator/ORCHESTRATOR_CONTRACT.md`.
- **AgentLifecycleProtocol** (Canonical): All agents MUST implement `cuga.agents.lifecycle.AgentLifecycleProtocol` defining startup/shutdown contracts (idempotent, timeout-bounded, error-safe), state ownership boundaries (AGENT/MEMORY/ORCHESTRATOR), and resource management guarantees. See `docs/agents/AGENT_LIFECYCLE.md` and `docs/agents/STATE_OWNERSHIP.md`.
- **AgentProtocol (I/O Contract)** (Canonical): All agents MUST implement `process(AgentRequest) -> AgentResponse` for standardized inputs (goal, task, metadata, inputs, context, constraints) and outputs (status, result/error, trace, metadata). Eliminates special-casing in routing/orchestration. See `docs/agents/AGENT_IO_CONTRACT.md`.
- **Failure Modes** (Canonical): All errors MUST be categorized using `FailureMode` taxonomy (AGENT/SYSTEM/RESOURCE/POLICY/USER), distinguishing retryable vs terminal failures and partial success states. Orchestrators MUST use `RetryPolicy` (exponential backoff/linear/none) for safe execution management. See `docs/orchestrator/FAILURE_MODES.md`.

## Orchestrator-Enhanced Agents (v1.3.2)

### CoordinatorAgent
CoordinatorAgent now integrates with RoutingAuthority for deterministic worker selection:

**Core Capabilities:**
- **RoutingAuthority Integration**: Delegates worker selection to pluggable `RoutingPolicy` implementations
- **Round-Robin Policy**: Thread-safe worker selection guaranteeing fairness across concurrent dispatches
- **Trace Propagation**: Ensures `trace_id` flows from plan → route → execute with no gaps
- **Observability**: Emits `route_decision` events with worker_id, policy type, and reasoning

**Usage Pattern:**
```python
from cuga.orchestrator.routing import PolicyBasedRoutingAuthority, RoundRobinPolicy

# Create routing authority with round-robin policy
routing_authority = PolicyBasedRoutingAuthority(
    worker_policy=RoundRobinPolicy()
)

# Coordinator delegates to routing authority
coordinator = CoordinatorAgent(routing_authority=routing_authority)

# Dispatch with automatic routing
worker = coordinator.dispatch(task, workers=worker_pool)
```

**Key Benefits:**
- No internal routing logic in CoordinatorAgent (separation of concerns)
- Pluggable policies (round-robin, capability-based, load-balanced)
- Thread-safe concurrent dispatch with deterministic ordering
- Full audit trail of routing decisions

See `docs/orchestrator/ROUTING_AUTHORITY.md` for routing policy examples.

### WorkerAgent
WorkerAgent now supports retry, recovery, and budget enforcement:

**Core Capabilities:**
- **RetryPolicy Integration**: Automatic retry with exponential/linear backoff for transient failures
- **Partial Result Recovery**: Checkpoint-based resume after failures with `execute_from_partial()`
- **Budget Enforcement**: Validates `ToolBudget` before tool calls, emits `budget_exceeded` on violation
- **Observability**: Emits `tool_call_start`, `tool_call_complete`, `tool_call_error` with duration tracking

**Usage Pattern:**
```python
from cuga.orchestrator.retry import create_retry_policy
from cuga.orchestrator.partial_result import PartialResult

# Create worker with retry policy
retry_policy = create_retry_policy(
    strategy="exponential",
    max_attempts=3,
    base_delay=0.1,
    max_delay=5.0,
)

worker = WorkerAgent(
    registry=registry,
    memory=memory,
    retry_policy=retry_policy,
)

# Execute with automatic retry
try:
    result = worker.execute(steps, metadata={"trace_id": trace_id})
except Exception as exc:
    # Extract partial result for recovery
    partial = worker.get_partial_result_from_exception(exc)
    if partial and partial.is_recoverable:
        # Resume from checkpoint
        result = worker.execute_from_partial(steps, partial)
```

**Key Benefits:**
- Transient failure handling without manual retry logic
- Preserves completed work for recovery (no redundant re-execution)
- Budget ceiling enforcement prevents runaway costs
- Rich observability for debugging execution failures

See `docs/orchestrator/FAILURE_MODES.md` for retry strategies and `tests/test_partial_results.py` for recovery examples.

### PlannerAgent
PlannerAgent now creates budget-aware plans with audit integration:

**Core Capabilities:**
- **ToolBudget Creation**: Plans include `cost_ceiling`, `call_ceiling`, `token_ceiling` enforcement
- **AuditTrail Integration**: All plans automatically recorded with trace_id and goal metadata
- **Observability**: Emits `plan_created` events with step_count, tool_list, budget_remaining

**Usage Pattern:**
```python
from cuga.orchestrator.planning import Plan, PlanStep, ToolBudget, PlanningStage

# Planner creates budget-aware plans
planner = PlannerAgent(registry=registry, memory=memory)

# Plan with budget constraints
plan = planner.plan(
    goal="Analyze user feedback and generate report",
    metadata={
        "trace_id": trace_id,
        "budget": ToolBudget(
            cost_ceiling=50.0,
            call_ceiling=20,
            token_ceiling=5000,
        ),
    },
)

# Plan automatically recorded to audit trail
assert plan.budget.cost_ceiling == 50.0
assert plan.stage == PlanningStage.CREATED
```

**Key Benefits:**
- Prevents unbounded tool usage with budget ceilings
- Full audit trail of planning decisions for debugging
- Observable plan creation with metadata tracking
- Explicit state machine (CREATED → VALIDATED → EXECUTING → COMPLETED)

See `docs/orchestrator/PLANNING_AUTHORITY.md` for planning patterns.

## Planning Protocol
- LangGraph-first planning and streaming hooks; planners must not select all tools blindly and must rank by similarity/metadata.
- Clamp `PLANNER_MAX_STEPS` to 1..50 with warnings on invalid input; `MODEL_TEMPERATURE` clamps to 0..2.

## Tool Contract
- Tools live under `cuga.modular.tools.*` only; signature `(inputs: Dict[str, Any], context: Dict[str, Any]) -> Any` with explicit schemas.
- No `eval`/`exec`, no network unless profile allows, and parameters must be declared with IO expectations.
- **HTTP Client (Canonical)**: All HTTP requests MUST use `cuga.security.http_client.SafeClient` wrapper with enforced timeouts (10.0s read, 5.0s connect), automatic retry with exponential backoff (4 attempts max, 8s max wait), and redirect following. No raw httpx/requests/urllib usage outside SafeClient. URL redaction in logs (strip query params/credentials).
- **Secrets Management (Canonical)**: All credentials MUST be env-only (no hardcoded secrets). CI enforces `.env.example` parity validation (no missing keys) and runs SECRET_SCANNER=on (trufflehog/gitleaks) on every push/PR. Secrets validated per execution mode (local/service/mcp/test) with helpful error messages. See `cuga.security.secrets` for enforcement.

## Memory & RAG
- Deterministic/local embeddings by default; metadata must include `path` and `profile`; isolation per profile with no cross-profile leakage.

## Agent Lifecycle & State Ownership
- **Lifecycle States**: Agents transition UNINITIALIZED → INITIALIZING → READY → BUSY → SHUTTING_DOWN → TERMINATED with atomic, logged transitions.
- **startup() Contract**: Must be idempotent, timeout-bounded, and atomic (rollback on error if `cleanup_on_error=True`); allocates resources, loads MEMORY state, initializes ephemeral AGENT state.
- **shutdown() Contract**: MUST NOT raise exceptions (log errors internally), completes within timeout, discards AGENT state (ephemeral), persists MEMORY state (dirty flush), notifies ORCHESTRATOR.
- **State Ownership Boundaries**:
  - **AGENT**: Request-scoped ephemeral state (current_request, temp_data, _internal_*) — discarded on shutdown, read/write by agent only.
  - **MEMORY**: Cross-request persistent state (user_history, embeddings, learned_facts) — survives restarts, agent read-only (write via `memory.update()`), memory system read/write.
  - **ORCHESTRATOR**: Trace-scoped coordination state (trace_id, routing_context, parent_context) — managed by orchestrator, agent read-only.
- **Violation Detection**: Agents MUST implement `owns_state(key) -> StateOwnership` and raise `StateViolationError` on mutation rule violations.
- **Testing Requirements**: All agents MUST pass lifecycle compliance tests (startup idempotency, shutdown error-safety, state ownership boundaries, resource cleanup verification).

## Orchestrator & Coordinator Policy
- **Canonical Contract**: All orchestrators MUST implement `OrchestratorProtocol` with explicit lifecycle stages, deterministic routing decisions, structured error handling (fail-fast/retry/fallback/continue) with failure mode categorization, and immutable `ExecutionContext` with trace_id propagation.
- **Execution Context (Canonical)**: All orchestration operations MUST use explicit `ExecutionContext` (defined in `cuga.orchestrator.protocol`) with required `trace_id` and optional `request_id`, `user_intent`, `user_id`, `memory_scope`, `conversation_id`, `session_id` fields. Context MUST be immutable (frozen dataclass) with `with_*` update methods. No implicit context in metadata dicts. Executors MUST import canonical `ExecutionContext` from orchestrator module. See `docs/orchestrator/EXECUTION_CONTEXT.md`.
- **Routing Authority (Canonical)**: All routing decisions MUST go through `RoutingAuthority` interface. Orchestrators delegate agent/worker/tool selection to pluggable `RoutingPolicy` implementations (round-robin, capability-based, load-balanced, etc.). No routing bypass allowed—agents/FastAPI/LangGraph nodes MUST NOT contain internal routing logic. See `docs/orchestrator/ROUTING_AUTHORITY.md`.
- **Planning Authority (Canonical)**: All planning decisions MUST go through `PlanningAuthority` interface with explicit Plan→Route→Execute state machine transitions. Plans MUST include `ToolBudget` tracking (cost/calls/tokens) with budget enforcement before execution. State transitions MUST be idempotent and validated. No implicit planning in orchestrators. See `docs/orchestrator/PLANNING_AUTHORITY.md`.
- **Audit Trail (Canonical)**: All routing and planning decisions MUST be recorded to persistent `AuditTrail` with decision reasoning, alternatives considered, and timestamps. Audit backends (JSON/SQLite) MUST support trace-based queries. No decision without audit record. See `docs/orchestrator/PLANNING_AUTHORITY.md`.
- **Failure Modes (Canonical)**: All failures MUST be categorized using `FailureMode` (agent/system/resource/policy/user errors) with clear retryable/terminal/partial-success semantics. Orchestrators delegate retry decisions to `RetryPolicy` implementations (ExponentialBackoff/Linear/NoRetry). Partial results MUST be preserved and recoverable. See `docs/orchestrator/FAILURE_MODES.md`.
- Thread-safe round-robin worker selection with preserved plan ordering and trace propagation across planner/worker/coordinator.
- Orchestrators delegate to ToolRegistry (tool resolution), PolicyEnforcer (validation), VectorMemory (memory), ObservabilityCollector (observability via `get_collector()`), **RoutingAuthority** (routing decisions), **PlanningAuthority** (plan creation), **AuditTrail** (decision recording), and **RetryPolicy** (retry logic) — MUST NOT directly call tool handlers, enforce policies, make routing decisions, create plans, or implement custom retry logic.

## Configuration Policy
- **Precedence Layers (Canonical)**: All configuration MUST follow explicit precedence order: CLI args > env vars > .env files > YAML configs > TOML configs > configuration defaults > hardcoded defaults. Unified ConfigResolver enforces precedence, deep merge for dicts, override for lists/scalars, and provenance tracking (which layer provided which value). No ad-hoc config reads bypassing resolver. See `docs/configuration/CONFIG_RESOLUTION.md`.
- **Config Sources (Documented)**: `config/` (Hydra registry fragments), `configs/` (agent/memory/RAG/observability), `configurations/` (MCP defs/policies/profiles), `.env`/`.env.mcp` (env overrides), `registry.yaml` (tool registry), `settings.toml`/`eval_config.toml` (backend settings). Loaders: Dynaconf (settings), Hydra (registry), direct YAML/TOML, dotenv. All sources MUST be documented with purpose, loader, and precedence layer.
- **Environment Requirements (Canonical)**: All execution modes MUST document required/optional/conditional environment variables. Local CLI requires model API key (OPENAI_API_KEY or provider-specific). Service mode requires AGENT_TOKEN (authentication) + AGENT_BUDGET_CEILING (budget enforcement) + model keys. MCP mode requires MCP_SERVERS_FILE (server definitions) + CUGA_PROFILE_SANDBOX (sandbox isolation) + model keys. Test mode requires no env vars (uses defaults/mocks). Validators MUST check requirements before startup per mode with helpful error messages suggesting missing vars. See `docs/configuration/ENVIRONMENT_MODES.md`.
- Env allowlist: `AGENT_*`, `OTEL_*`, `LANGFUSE_*`, `OPENINFERENCE_*`, `TRACELOOP_*`; budget ceilings default 100 with escalation max 2 and `warn|block` budget policy.
- Sandbox profiles (`py/node slim|full`, `orchestrator`) must be declared per registry entry with `/workdir` pinning for exec scopes and read-only defaults.

## Observability & Tracing
- Structured, PII-safe logs with redaction for `secret`, `token`, `password` keys; `trace_id` propagates through CLI, planner, worker, coordinator, and tools.
- Emit spans for plan creation, tool selection, execution start/stop, backend calls, registry/budget decisions; default OTEL/LangFuse/LangSmith hooks from env.
- **Structured Events (Canonical)**: All lifecycle operations MUST emit structured events via `cuga.observability.emit_event()`. Event types: `plan_created`, `route_decision`, `tool_call_start`, `tool_call_complete`, `tool_call_error`, `budget_warning`, `budget_exceeded`, `approval_requested`, `approval_received`, `approval_timeout`. Events MUST include `trace_id`, `timestamp`, `event_type`, and optional `duration_ms`. See `docs/observability/OBSERVABILITY_SLOS.md`.
- **Golden Signals (Canonical)**: All orchestrators MUST track golden signals via `cuga.observability.GoldenSignals`: success_rate (% successful), latency (P50/P95/P99), tool_error_rate (% failed tool calls), mean_steps_per_task, approval_wait_time, budget_utilization. Metrics MUST be exportable to Prometheus format and OTEL backends. See `docs/observability/OBSERVABILITY_SLOS.md`.
- **OTEL Export (Canonical)**: All events MUST be exportable to OpenTelemetry backends (OTLP, Jaeger, Zipkin) via `cuga.observability.OTELExporter`. Exporters MUST support environment-based configuration (`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, `OTEL_TRACES_EXPORTER`). Console exporter MUST be default for offline-first operation. No network I/O required for observability. See `docs/observability/OBSERVABILITY_SLOS.md`.
- **Observability Collector (Canonical)**: All components MUST use `cuga.observability.ObservabilityCollector` singleton via `get_collector()`. Collector MUST be thread-safe, support auto-export, buffer events (default 1000), and flush on shutdown. Initialization MUST occur at startup with `set_collector()`. See `docs/observability/INTEGRATION_CHECKLIST.md`.
- **PII Redaction (Canonical)**: All events MUST auto-redact sensitive keys (`secret`, `token`, `password`, `api_key`, `credential`, `auth`, `authorization`, `bearer`) before emission. Redaction MUST be applied recursively to nested dicts. No PII in event payloads, attributes, or error messages.
- **Grafana Dashboard (Canonical)**: Default dashboard MUST be provided at `observability/grafana_dashboard.json` with panels for success_rate, latency percentiles, tool_error_rate, mean_steps_per_task, approval_wait_time, budget_utilization, tool errors by type/tool, request rate, and event timeline. Dashboard MUST support profile-based filtering.
- **Prometheus Metrics (Canonical)**: Metrics endpoint MUST expose Prometheus text format via `get_collector().get_prometheus_metrics()`. Metrics: `cuga_requests_total`, `cuga_success_rate`, `cuga_latency_ms`, `cuga_tool_error_rate`, `cuga_steps_per_task`, `cuga_tool_calls_total`, `cuga_tool_errors_total`, `cuga_approval_requests_total`, `cuga_approval_wait_ms`, `cuga_budget_warnings_total`, `cuga_budget_exceeded_total`.

## Testing Invariants
- Tests cover import guardrails (reject non-`cuga.modular.tools.*`), planner ranking, round-robin scheduling, env parsing clamps, registry determinism, and sandbox profile enforcement.
- Run `python scripts/verify_guardrails.py --base <ref>` plus stability harness before merging guardrail or registry changes.

## Change Management
- Guardrail/registry updates require synced docs (`README.md`, `PRODUCTION_READINESS.md`, `CHANGELOG.md`, `todo1.md`) and migration notes; update `AGENTS.md` first.
- Developer checklist: document registry edits, budget/observability env wiring, sandbox mounts, and add/refresh tests plus `docs/mcp/tiers.md` table regeneration.

## 1. Scope & Precedence
- Root guardrails are canonical for all subdirectories; add directory-specific `AGENTS.md` only to tighten rules, never to relax them.
- Allowlisted tools live under `cuga.modular.tools.*`; any denylisted or unknown module import MUST be rejected before execution.
- Tier 1 defaults are enabled only when allowlists/denylists, escalation ceilings, secret redaction, and budget caps are present and in sync with the registry.
- Registry edits are the sole mechanism for tool swaps; hot swaps MUST go through registry.yaml diffs with deterministic ordering.
- PlannerAgent accepts `(goal: str, metadata: dict)` and returns an ordered plan with streaming-friendly traces; WorkerAgent executes ordered steps; CoordinatorAgent preserves trace ordering with thread-safe round-robin worker selection.

## 2. Profile Isolation
- MUST run deterministically offline; avoid network after setup; mock/record external calls.
- MUST prioritize security-first designs: least privilege, sanitized inputs, no `eval`/`exec`.
- MUST keep memory/profile data isolated per profile; no cross-profile leakage; default profile falls back to `memory.profile` when unspecified.

## 3. Registry Hygiene
- Registry entries MUST declare sandbox profile (`py/node slim|full`, `orchestrator`), read-only mounts, and `/workdir` pinning for exec sandboxes.
- Compose mounts/env for Tier 1 entries MUST match `docs/mcp/registry.yaml` and include health checks; Tier 2 entries default to `enabled: false`.
- Env keys MUST wire observability (`OTEL_*`, LangFuse/LangSmith) and budget enforcement (`AGENT_*`) with `warn|block` policies spelled out.
  Current policy: allowlist `cuga.modular.tools.*` only; denylist any external module imports; env allowlist `AGENT_*`, `OTEL_*`,
  `LANGFUSE_*`, `OPENINFERENCE_*`, `TRACELOOP_*`. Budget ceilings default `AGENT_BUDGET_CEILING=100`, escalation max `AGENT_ESCALATION_MAX=2`,
  and redaction removes values matching `secret`, `token`, or `password` keys before logging.

## 4. Sandbox Expectations
- Tool handler signature: `(inputs: Dict[str, Any], context: Dict[str, Any]) -> Any`; context includes `profile`, `trace_id`.
- Dynamic imports MUST be restricted to `cuga.modular.tools.*`; reject relative/absolute paths outside this namespace and denylisted modules.
- Tools MUST declare parameters/IO expectations; MUST NOT perform network I/O unless explicitly allowed by profile; honor budget ceilings and redaction rules for outputs/logs.
- Forbidden: `eval`/`exec`, writing outside sandbox, spawning daemons, or swallowing errors silently; read-only mounts are the default.
- **Eval/Exec Elimination (Canonical)**: Direct `eval()` and `exec()` calls are FORBIDDEN in all production code paths. Expression evaluation MUST use `cuga.backend.tools_env.code_sandbox.safe_eval.safe_eval_expression()` (AST-based, allowlist operators/functions). Code execution MUST use `cuga.backend.tools_env.code_sandbox.safe_exec.SafeCodeExecutor` or `safe_execute_code()` with enforced import allowlists (only `cuga.modular.tools.*`), restricted builtins (no eval/exec/open/compile/__import__), filesystem deny-by-default, timeout enforcement, and audit trail. All code execution is routed through these abstractions with trace propagation.
- **HTTP Enforcement**: Network I/O MUST use `SafeClient` from `cuga.security.http_client` with enforced timeouts (10.0s read, 5.0s connect, 10.0s write, 10.0s total), automatic exponential backoff retry (4 attempts, 8s max wait), and URL redaction. Raw httpx/requests calls rejected.
- **Secrets Enforcement**: Credentials MUST be loaded from environment variables only. Hardcoded API keys/tokens/passwords trigger CI failure. All secret values redacted in logs/errors per `cuga.security.secrets.redact_dict()`.

## 5. Audit / Trace Semantics
- Logs MUST be structured (JSON-friendly) and omit PII; redact secrets before emission; include reason when budgets trigger warn/block decisions.
- `trace_id` MUST propagate across planner/worker/coordinator, CLI, and tools with ordered plan traces preserved under concurrency.
- Emit events for plan creation, tool selection, execution start/stop, backend connections, errors, and budget/registry decisions.

## 6. Documentation Update Rules
- Config changes MUST update tests and docs in the same PR; env parsing MUST clamp `PLANNER_MAX_STEPS` to 1..50 and `MODEL_TEMPERATURE` to 0..2 with warnings on invalid values.
- Edit `AGENTS.md` first when modifying guardrails; update `CHANGELOG.md` (`## vNext`) with summary and keep migration notes current for breaking changes.
- Document registry and sandbox guardrail adjustments in `CHANGELOG.md` alongside updated tests.
- Keep contributor-facing docs synchronized with guardrail expectations: refresh README/PRODUCTION readiness notes and the repo to-do tracker (`todo1.md`) when altering registry allowlists, budgets, or redaction policies. Guardrail/registry diffs now fail CI unless `README.md`, `PRODUCTION_READINESS.md`, `CHANGELOG.md`, and `todo1.md` are updated in the same PR and `scripts/verify_guardrails.py --base <ref>` passes locally.

## 7. Verification & No Conflicting Guardrails
- Tests MUST assert planner does not return all tools blindly; vector scores correlate with similarity and are ordered.
- Round-robin coordinator scheduling MUST be verified under concurrent calls; planner/worker/coordinator interface guardrails MUST be covered by automated checks.
- Import guardrails MUST be enforced (reject non-`cuga.modular.tools.*`); env parsing tests MUST cover invalid/edge values and fallback behavior.
- Any change violating or adjusting guardrails MUST update this file plus corresponding tests in the same PR; non-root `AGENTS.md` MUST only declare inheritance, never canonical status.
- **Test Coverage Requirements (Canonical)**: All architectural layers MUST maintain >80% test coverage. Critical orchestration paths (planning → execution, profile-based isolation, memory-augmented planning) MUST have integration tests. Untested layers (tools, memory, config, observability) block production deployment. See `docs/testing/COVERAGE_MATRIX.md` for layer-by-layer coverage analysis, critical path validation, and priority roadmap. Each layer MUST have assigned test ownership.
- **Scenario Testing Requirements (Canonical)**: All agent composition patterns (multi-agent dispatch, memory-augmented planning, profile-based isolation, error recovery, stateful conversations, complex workflows, nested coordination) MUST have end-to-end scenario tests with real components (minimal mocks). Scenario tests validate orchestration logic under real conditions with memory persistence, tool execution chains, and failure recovery patterns. See `docs/testing/SCENARIO_TESTING.md` for scenario catalog, test patterns, and coverage goals.

## 8. Contributor Checklist (TL;DR)
- Read this file first and confirm registry/sandbox edits follow the allowlist/denylist rules.
- Keep docs (README, PRODUCTION readiness, security/policies) and `todo1.md` aligned with any guardrail or registry change.
- Run `python scripts/verify_guardrails.py` and the stability harness before merging; add new tests when planner/worker/coordinator interfaces evolve.

---

## 9. v1.1 Agent Integration (COMPLETED in v1.1.0 - 2026-01-02)

**v1.1.0 Release Status:** ✅ **COMPLETE** - All modular agents (`src/cuga/modular/agents.py`) are now fully integrated with observability and guardrails infrastructure.

### What Was Delivered

- ✅ **PlannerAgent Observability**: Emits `plan_created` events with metadata (goal, steps_count, tools_selected, duration_ms, profile)
- ✅ **WorkerAgent Observability**: Emits `tool_call_start`, `tool_call_complete`, `tool_call_error` events for all tool executions
- ✅ **WorkerAgent Guardrails**: Enforces budget constraints with `budget_guard()`, emits `budget_exceeded` events
- ✅ **CoordinatorAgent Observability**: Emits `route_decision` events with routing metadata
- ✅ **Integration Tests**: 11 comprehensive tests (26/26 total tests passing - 100%)
- ✅ **Documentation**: Complete agent integration guide at `docs/observability/AGENT_INTEGRATION.md`

### Deprecation Notice

**Legacy observability patterns are deprecated as of v1.1.0 and will be removed in v1.3.0:**

- `BaseEmitter` (use `cuga.observability.emit_event()` instead)
- `InMemoryTracer` (use `cuga.observability.get_collector()` instead)
- `WorkerAgent.observability` parameter (events now automatically emitted)

**Migration guide:** See `docs/observability/AGENT_INTEGRATION.md` for complete migration instructions and examples.

**Backward Compatibility:** All legacy patterns emit deprecation warnings but remain functional until v1.3.0 removal.

