# 📦 CHANGELOG

All notable changes to the CUGAR Agent project will be documented in this file.
This changelog follows the guidance from [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

---

## vNext
- **Added canonical OrchestratorProtocol**: Defined single source of truth for orchestration with explicit lifecycle stages (initialize/plan/route/execute/aggregate/complete), typed routing decisions, structured error propagation, and immutable ExecutionContext. See `docs/orchestrator/ORCHESTRATOR_CONTRACT.md` and `src/cuga/orchestrator/protocol.py`.
- **Added Explicit Execution Context**: Formalized `ExecutionContext` with explicit fields for `request_id`, `user_intent`, `user_id`, `memory_scope`, `conversation_id`, `session_id`, and `created_at` timestamp. Replaces implicit context (scattered across metadata dicts, HTTP headers, ActivityTracker, MemoryStore) with single immutable, type-checked structure. Enables comprehensive observability and safe orchestration with trace continuity via `parent_context` chaining. All executors MUST import canonical `ExecutionContext` from `cuga.orchestrator.protocol`. See `docs/orchestrator/EXECUTION_CONTEXT.md`.
- **Added Unified Configuration Resolution Strategy**: Documented explicit precedence layers (CLI args > env vars > .env > YAML > TOML > defaults > hardcoded) unifying scattered config sources (`config/`, `configs/`, `configurations/`, `.env.example`, `.env.mcp`, `registry.yaml`, `settings.toml`). ConfigResolver enforces precedence, deep merge for dicts, override for lists/scalars, schema validation, and provenance tracking (observability for "where did this value come from"). Eliminates ad-hoc `os.getenv()` bypassing resolution order. See `docs/configuration/CONFIG_RESOLUTION.md`.
- **Added Environment Variable Requirements Documentation**: Documented required/optional/conditional environment variables per execution mode (local CLI, service, MCP orchestration, test). Local mode requires model API key with optional profile/vector/observability vars. Service mode requires AGENT_TOKEN (authentication), AGENT_BUDGET_CEILING (budget enforcement), model keys, with recommended observability. MCP mode requires MCP_SERVERS_FILE (server definitions), CUGA_PROFILE_SANDBOX (sandbox isolation), model keys. Test mode requires no env vars (uses defaults and mocks). Includes validation script for each mode, troubleshooting guide, migration from ad-hoc to mode-specific environments, CI/CD examples. Reduces deployment friction, prevents production failures from missing required vars, clarifies CI/CD setup expectations. See `docs/configuration/ENVIRONMENT_MODES.md`.
- **Added Test Coverage Matrix**: Documented test coverage mapped to architectural responsibilities (orchestrator/agents/tools/memory/config/observability). Orchestrator 80% covered (35+ tests), agents 60% covered (30+ tests), failure modes 85% covered (60+ tests), routing 80% covered (50+ tests). Critical gaps identified: tools layer 10% covered (security boundary untested), memory layer 0% covered (data persistence untested), config layer 0% covered (precedence untested), observability 0% covered (trace propagation untested). Analyzed 6 critical orchestration paths (planning→execution, multi-worker coordination, nested orchestration, error recovery, memory-augmented planning, profile-based isolation) with end-to-end test status. Provides priority roadmap (16 hours for critical gaps, 24 hours for untested layers, 40 hours for integration suite). Identified production deployment blockers: tools security boundaries, memory data integrity, profile isolation. See `docs/testing/COVERAGE_MATRIX.md`.
- **Added Scenario-Level Tests for Agent Composition**: Implemented 8 end-to-end scenario test suites (13 tests total, 650+ lines) validating orchestration logic under real conditions with real components (minimal mocks). Scenarios cover: multi-agent dispatch (CrewAI/AutoGen style round-robin coordination with 3+ workers), memory-augmented planning (vector similarity influencing tool ranking), profile-based isolation (security boundaries per execution profile with no cross-contamination), error recovery (tool failures, retries, partial results), streaming execution (event emission during planning/execution), stateful multi-turn conversations (session persistence with context carryover), complex multi-step workflows (5+ step data pipelines), and nested coordination (parent → child orchestrators with shared memory). All tests use real PlannerAgent/WorkerAgent/CoordinatorAgent/VectorMemory components, validate trace propagation, and check memory persistence. Provides test patterns, fixtures, troubleshooting guide, and coverage goals. See `tests/scenario/test_agent_composition.py` and `docs/testing/SCENARIO_TESTING.md`.
- **Added System Execution Narrative**: Created comprehensive "Request → Response" flow documentation tracing complete execution from entry points (CLI/FastAPI/MCP) through routing, planning, coordination, execution, memory operations, tool execution, and response assembly. Unifies scattered architecture docs into single contributor onboarding guide. Covers: 3 entry point modes with environment requirements, ExecutionContext creation and propagation, RoutingAuthority decisions, PlannerAgent tool ranking with memory-augmented search, CoordinatorAgent round-robin worker selection, WorkerAgent sandboxed execution with budget enforcement, VectorMemory search/remember operations with profile isolation, tool handler execution patterns (local + MCP), trace propagation across all layers, observability integration (OTEL/LangFuse/LangSmith), security boundaries (sandbox profiles, allowlists, budget ceilings), performance considerations (concurrency, memory management, observability overhead), debugging tips (trace correlation, memory inspection, routing verification), and testing guidance (unit + scenario tests). Includes complete flow diagram, security checklists, and links to 20+ related docs. See `docs/SYSTEM_EXECUTION_NARRATIVE.md`.
- **Clarified FastAPI's Architectural Role**: Created comprehensive documentation explicitly defining FastAPI as transport layer only (not orchestrator) to prevent mixing transport and orchestration concerns. Clarifies FastAPI's canonical responsibilities: HTTP/SSE transport (endpoints, streaming), authentication (X-Token validation), budget enforcement (AGENT_BUDGET_CEILING middleware), trace propagation (observability hooks), and request/response serialization. Documents what FastAPI must NOT do: planning logic (belongs in PlannerAgent), coordination decisions (belongs in CoordinatorAgent), tool execution (belongs in WorkerAgent), tool resolution (belongs in ToolRegistry), or memory operations (belongs in VectorMemory). Provides architectural layer diagram showing clear separation between transport (FastAPI) and orchestration (Planner/Coordinator/Workers), delegation patterns for synchronous planning/streaming execution/LangGraph integration, anti-patterns showing incorrect mixing of concerns, security boundary clarification (FastAPI enforces auth + budget, orchestration enforces profile isolation + tool allowlists), and testing implications (test transport and orchestration layers separately). Includes comparison table, code examples, and golden rule: "If it's not about HTTP transport, auth, or budget enforcement, it doesn't belong in FastAPI." See `docs/architecture/FASTAPI_ROLE.md`.
- **Added canonical RoutingAuthority**: Centralized routing decision authority eliminating distributed logic across coordinators, agents, and FastAPI endpoints. All routing decisions MUST go through `RoutingAuthority` with pluggable policies (round-robin, capability-based, load-balanced). Orchestrators delegate routing to `RoutingAuthority`, no routing bypass allowed. See `docs/orchestrator/ROUTING_AUTHORITY.md` and `src/cuga/orchestrator/routing.py`.
- **Added canonical Failure Modes and Retry Semantics**: Comprehensive failure taxonomy (`FailureMode`) categorizing agent/system/resource/policy/user errors with clear retryable/terminal/partial-success semantics. Introduced pluggable `RetryPolicy` (ExponentialBackoff/Linear/NoRetry) with auto-detection, jitter, circuit breaker integration. `PartialResult` preserves partial execution for recovery. See `docs/orchestrator/FAILURE_MODES.md` and `src/cuga/orchestrator/failures.py`.
- **Added canonical AgentLifecycleProtocol**: Clarified agent startup/shutdown expectations with idempotent, timeout-bounded, error-safe contracts. Defined state ownership boundaries (AGENT/MEMORY/ORCHESTRATOR) resolving ambiguity between ephemeral, persistent, and coordination state. See `docs/agents/AGENT_LIFECYCLE.md`, `docs/agents/STATE_OWNERSHIP.md`, and `src/cuga/agents/lifecycle.py`.
- **Added canonical AgentProtocol (I/O Contract)**: Standardized agent inputs (AgentRequest with goal/task/metadata/inputs/context/constraints) and outputs (AgentResponse with status/result/error/trace/metadata) eliminating special-casing in routing/orchestration. See `docs/agents/AGENT_IO_CONTRACT.md` and `src/cuga/agents/contracts.py`.
- Added guardrail enforcement utilities, sandbox allowlist, and coverage gating to 80%.
- Added CI enforcement so guardrail and registry diffs fail when documentation or changelog updates are missing.
- Introduced LangGraph-style planner/coordinator stack with trace propagation, vector memory retention, and FastAPI deployment surface.
- Registry defaults now wire budget/observability env keys with validated sandbox profiles, `/workdir` pinning for exec scopes, deterministic hot-reload ordering, and refreshed guardrail documentation/developer checklist.

### Added
- ➕ Added: Explicit `ExecutionContext` with 12 fields (trace_id, request_id, user_intent, user_id, memory_scope, conversation_id, session_id, profile, metadata, parent_context, created_at) replacing scattered implicit context. Immutable frozen dataclass with `with_*` update methods (with_user_intent/with_request_id/with_profile/with_metadata), validation (trace_id required, memory_scope requires user_id, conversation_id requires session_id), and serialization (to_dict/from_dict). Eliminates duplicate ExecutionContext in `src/cuga/agents/executor.py` — all code MUST import from `cuga.orchestrator.protocol`. Documented in `docs/orchestrator/EXECUTION_CONTEXT.md`.
- ➕ Added: Deterministic hashing embedder and pluggable vector backends with local search fallback.
- ➕ Added: Secure modular CLI for ingest/query/plan with trace propagation and JSON logs.
- ➕ Added: Guardrail checker and AGENTS.md SSOT for modular stack.
- ➕ Added: Modular `cuga.modular` package with planner/worker/tool/memory/observability scaffolding ready for LangGraph/LangChain
- ➕ Added: Vector memory abstraction with in-memory fallback and optional Chroma/Qdrant/Weaviate/Milvus connectors
- ➕ Added: LlamaIndex RAG loader/retriever utilities and Langfuse/OpenInference observability hooks
- ➕ Added: Developer tooling (.editorconfig, .gitattributes, pre-commit config, expanded Makefile) and CI workflow `ci.yml`
- ➕ Added: Watsonx Granite provider scaffold, Langflow component stubs, registry validation starter, and sandbox profile JSON.
- ➕ Added: Templates and documentation for `.env`, roadmap, and multi-agent examples under `agents/`, `tools/`, `memory/`, and `rag/`
- In development: GitHub Actions CI, coverage reports, Langflow project inspector
- ➕ Added: `scrape_tweets` MCP tool using `snscrape` for Twitter/X scraping
- ➕ Added: `extract_article` MCP tool powered by `newspaper4k` style extraction
- ➕ Added: `crypto_wallet` MCP tool wrapper for mnemonic, derivation, and signing flows
- ➕ Added: `moon_agents` MCP tool exposing agent templates and plan scaffolds
- ➕ Added: `vault_tools` MCP tool bundle for JSON queries, KV storage, and timestamps
- ➕ Added: CLI for listing agents, running goals, and exporting structured results
- ➕ Added: External tool plugin system with discovery helpers and a template plugin example
- ➕ Added: Env-gated MCP registry loader/runner wiring with sample `registry.yaml` and planner/executor integration
- ➕ Added: Watsonx model settings template with deterministic default parameters for Granite.
- ➕ Added: Agent UI intent preview, invocation timeline, and state badge for clearer tool legibility
- ➕ Added: Expanded guardrail verification script (`scripts/verify_guardrails.py`), inheritance markers, and CI enforcement
- ➕ Added: Guardrail verifier coverage for allowlist/denylist, budget, escalation, and redaction keywords plus planner/worker/coordinator contracts
- ➕ Added: Dual-mode LLM adapter layer with hybrid routing, budget guardrails, and config/env precedence
- ➕ Added: Architecture/registry observability documentation set (overview, registry, tiers, sandboxes, compose, ADR, glossary)
- ➕ Added: MCP v2 registry slice with immutable snapshot models, YAML loader, and offline contract tests

### Changed
- 🔁 Changed: Planner, coordinator, worker, and RAG pipelines to enforce profile/trace propagation and round-robin fairness.
- 🔁 Changed: Dynamic tool imports hardened to `cuga.modular.tools.*` namespace with explicit errors.
- 🔁 Changed: Centralized MCP server utilities for payload handling and sandbox lookup
- 🔁 Changed: Planner now builds multi-step plans with cost/latency optimization, logging, and trace outputs
- 🔁 Changed: Controller and executor now emit structured audit traces and sanitize handler failures
- 🔁 Changed: Tool registry now deep-copies resolved entries and profile snapshots to prevent caller mutations from leaking between tools
- 🔁 Changed: Reconciled agent lifecycle, tooling, and security documentation with current code enforcement boundaries
- 🔁 Changed: Guardrail hierarchy documented explicitly in root/docs `AGENTS.md` with inheritance reminders.
- 🔁 Changed: Guardrail routing updated so root `AGENTS.md` remains canonical with per-directory inherit markers
- 🔁 Changed: Guardrail verification now centralizes allowlists/keywords and supports env overrides to reduce drift
- 🔁 Changed: Guardrail verification now tracks `config/` with inheritance markers to cover Hydra registry defaults
- 🔁 Changed: Root `AGENTS.md` reorganized to align Tier 1 defaults with registry tool swaps, sandbox pinning, and budget/redaction guardrails
- 🔁 Changed: Pytest default discovery now targets `tests/`, with docs/examples suites run through dedicated scripts and build artifacts ignored by default
- 🔁 Changed: Pytest `norecursedirs` now retains default exclusions (e.g., `.*`, `venv`, `dist`, `*.egg`) to avoid unintended test discovery
- 🔁 Changed: LLM adapter can run atop LiteLLM by default with hardened retries, fallback error handling, and thread-safe budget warnings
- 🔁 Changed: MCP registry loader now uses Hydra's `compose` API for Hydra/OmegaConf configuration composition with shared config defaults and fragment support
- 🔁 Changed: Watsonx Granite provider now validates credentials up front, enforces deterministic defaults, and writes structured audit metadata (timestamp, actor, parameters, outcome).
- 🔁 Changed: Tool registry loader parses files by extension (YAML/JSON) with optional schema validation guarded by dependency detection.
- 🔁 Changed: JSON Schema validation now guards registry parsing with structured logging and skips malformed entries instead of failing globally.
- 🔁 Changed: Watsonx function-call validation now fails fast by default with optional legacy graceful mode.

### Fixed
- 🐞 Fixed: Hardened `crypto_wallet` parameter parsing and clarified non-production security posture
- 🐞 Fixed: `extract_article` dependency fallback now respects missing `html` inputs
- 🐞 Fixed: `moon_agents` no longer returns sandbox filesystem paths
- 🐞 Fixed: `vault_tools` KV store now uses locked, atomic writes to avoid race conditions
- 🐞 Fixed: `vault_tools` detects corrupt stores, enforces locking support, and writes under held locks
- 🐞 Fixed: `vault_tools` KV store writes use fsynced temp files to preserve atomic persistence safety
- 🐞 Fixed: `_shared` CLI argument parsing now errors when `--json` is missing a value
- 🐞 Fixed: `crypto_wallet` narrows `word_count` parsing errors to expected types
- 🐞 Fixed: `_shared.load_payload` narrows JSON parsing exceptions for clearer diagnostics
- 🐞 Fixed: `extract_article` fallback parsing now only triggers for expected extraction or network failures
- 🐞 Fixed: Guardrail checker git diff detection now validates git refs and uses fixed git diff argv to avoid unchecked subprocess input
- 🐞 Fixed: Tier table generation now falls back to env keys for non-placeholder values to avoid leaking secrets in docs
- 🐞 Fixed: MCP registry loader enforces enabled-aware duplicate detection, method/path type validation (including `operation_id`), and environment variables that override disabled entries when set
- 🐞 Fixed: Guard modules deduplicated under a shared orchestrator to keep routing logic consistent across inputs, tools, and outputs.

### Documentation
- 📚 Rewrote README/USAGE/AGENTS/CONTRIBUTING/SECURITY with 2025 agent-stack guidance and integration steps
- 📚 Documented: Branch cleanup workflow and issue stubs for consolidating Codex branches
- 📚 Documented: Root guardrails, audit expectations, and routing table for guardrail updates
- 📚 Documented: Guardrail verification and change-management checklist in AGENTS/README plus alignment reminder in `todo1.md`
- 📚 Documented: Hydra-based registry composition (env overrides, enabled-only duplicate detection) and linked MCP integration guidance
- 📚 Documented: Refined canonical `AGENTS.md` with quick checklist, local template, and cross-links to policy docs
- 📚 Documented: Architecture topology (controller/planner/tool bus), orchestration modes, and observability enhancements
- 📚 Documented: STRIDE-lite threat model and red-team checklist covering sandbox escape, prompt injection, and leakage tests
- 📚 Documented: Usage and testing quick-start guides plus repository Code of Conduct and security policy
- 📚 Documented: Langflow guard components now use `lfx.*` imports with unique identifiers; registry and watsonx docs refreshed for extension-aware parsing and audit trails.

### Testing
- 🧪 Added: Unit tests for vector search scoring, planning relevance, round-robin dispatch, env parsing, and CLI flow.
- 🧪 Added: Expanded `scrape_tweets` test coverage for limits, dependencies, and health checks
- 🧪 Added: Offline MCP registry, runner, and planner/executor tests backed by FastAPI mock servers
- 🧪 Added: Dedicated lint workflow running Ruff and guardrail verification on pushes and pull requests

---

## [v1.0.0] - Initial Production Release

🎉 This is the first production-ready milestone for the `cugar-agent` framework.

### ✨ Added
- Modular agent pipeline:
  - `controller.py` – agent orchestration
  - `planner.py` – plan step generator
  - `executor.py` – tool execution
  - `registry.py` – tool registry and sandboxing
- Profile-based sandboxing with scoped tool isolation
- MCP-ready integrations and registry templating
- Profile fragment resolution logic (relative to profile path)
- PlantUML message flow for documentation
- Developer-friendly `Makefile` for env, profile, and registry tasks
- Initial tests in `tests/` for agent flow verification
- ➕ Added: Profile policy enforcer with schema validation and per-profile templates under `configurations/policies`

### 🛠️ Changed
- Standardized folder structure under `src/cuga/`
- Updated `.env.example` for MCP setup

### 📚 Documentation
- Rewritten `AGENTS.md` as central contributor guide
- Added structure for:
  - `agent-core.md`
  - `agent-config.md`
  - `tools.md`
- Registry merge guide in `docs/registry_merge.md`
- Security policy in `docs/Security.md`
- ➕ Added: `docs/policies.md` describing policy authoring and enforcement flow

### ⚠️ Known Gaps
- CLI runner may need test scaffolding
- Tool schema validation needs stronger contract enforcement
- Logging verbosity defaults may need hardening

---
