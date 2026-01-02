# Repository To-Do (v1.0.0 SHIPPED ✅ → v1.1 Planning)

**Last Updated:** 2026-01-02  
**v1.0.0 Status:** ✅ **SHIPPED** (Security Hardening & Observability Complete)  
**v1.1 Status:** Planning (Protocol Integration & Scenario Testing)

---

## ✅ v1.0.0 Completed Tasks (SHIPPED 2026-01-02)

### Governance & Guardrails ✅
- [x] Guardrails enforcement system (allowlist-first, parameter schemas, risk tiers, budget tracking)
- [x] HTTP hardening with SafeClient (enforced timeouts, automatic retry, URL redaction)
- [x] Secrets management (env-only, CI scanning with trufflehog + gitleaks, `.env.example` parity)
- [x] Eval/exec elimination (AST-based safe_eval_expression, SafeCodeExecutor with allowlists)
- [x] Root `AGENTS.md` aligned with guardrail enforcement (sandbox deny-by-default, PII redaction, approval gates)
- [x] Guardrail CI gate (registry/AGENTS edits fail unless docs updated and `scripts/verify_guardrails.py` passes)

### Registry & Sandbox Enablement ✅
- [x] Registry-driven hot-swap flow (tool replacements via registry edits only, deterministic ordering)
- [x] Sandbox profiles enforced per registry entry (py/node slim/full, read-only mounts, `/workdir` pinning)
- [x] Observability and budget enforcement env keys wired (`AGENT_*`, `OTEL_*`, LangFuse/LangSmith)

### Observability & Tracing ✅
- [x] Comprehensive observability system (OTEL integration, Prometheus `/metrics`, Grafana dashboard with 12 panels)
- [x] Golden signals tracking (success rate, latency P50/P95/P99, tool error rate, mean steps per task, approval wait time)
- [x] Structured events (14 event types: plan, route, tool_call, budget, approval, execution, memory)
- [x] PII-safe logging with automatic redaction (secret/token/password keys recursively redacted)
- [x] Trace propagation (`trace_id` flows through all operations, thread-safe collector)

### Configuration & Testing ✅
- [x] Config precedence enforcement (CLI > env > .env > YAML > TOML > defaults with ConfigResolver)
- [x] Config precedence tests (40+ tests validating resolution order and provenance tracking)
- [x] Tools/registry coverage (tests for tool selection, parameter validation, budget tracking)
- [x] Memory/RAG coverage (tests for profile isolation, retention, vector backend switching)
- [x] Observability tests (36 tests for events, golden signals, collector integration)
- [x] Guardrails tests (30+ tests for allowlists, schemas, egress, budget, approval)

### Deployment & Documentation ✅
- [x] Kubernetes manifests (deployment, services, configmaps, secrets, namespace, health checks)
- [x] Docker-compose image pinning (CI blocks `:latest` tags)
- [x] PRODUCTION_READINESS.md updated (rollout/rollback procedures, resource requirements)
- [x] SECURITY.md updated (6 new sections: sandbox, parameters, network egress, PII, approvals, secrets)
- [x] CHANGELOG.md v1.0.0 release notes (comprehensive feature summary)
- [x] USAGE.md updated (config precedence, guardrail examples)
- [x] PROTOCOL_INTEGRATION_STATUS.md created (protocol status, v1.1 roadmap)

**Total v1.0.0 Work:** 8 major tasks, 2,640+ test lines, 130+ tests, 7 documentation files updated

---

## 📋 v1.1 Roadmap (Protocol Integration & Scenario Testing)

### Protocol Integration (2-4 weeks)

**Goal:** Wire existing protocols into legacy agents without breaking changes

**Approach:** Pragmatic shims (not full rewrite)

#### Phase 1: Shim Layer (Week 1 — 2 days)
- [ ] Add `AgentLifecycleProtocol` shims to `PlannerAgent`/`WorkerAgent`/`CoordinatorAgent`
  - [ ] Add `startup()` method (no-op initially, can add resource initialization later)
  - [ ] Add `shutdown()` method (no-op initially, can add cleanup later)
  - [ ] Add `owns_state(key)` method (return `StateOwnership.AGENT` for all keys initially)
- [ ] Add `process(AgentRequest) -> AgentResponse` wrapper methods
  - [ ] `PlannerAgent.process()` wraps existing `plan(goal, metadata)`
  - [ ] `WorkerAgent.process()` wraps existing `execute(steps, metadata)`
  - [ ] `CoordinatorAgent.process()` wraps existing `dispatch(goal, trace_id)`
- [ ] Maintain backward compatibility (existing `plan()`/`execute()`/`dispatch()` still work)

#### Phase 2: Compliance Tests (Week 1 — 2 days)
- [ ] Create `tests/agents/test_protocol_compliance.py` (20 essential tests)
  - [ ] 5 tests: Agents accept `AgentRequest`, return `AgentResponse`
  - [ ] 5 tests: Lifecycle methods exist and are callable (startup/shutdown idempotent)
  - [ ] 5 tests: `ExecutionContext` propagates through operations
  - [ ] 5 tests: Error handling returns structured `AgentError`

#### Phase 3: Gradual Migration (Week 2-3 — ongoing)
- [ ] Update orchestrator to use `ExecutionContext` instead of raw metadata dicts
- [ ] Wire `RoutingAuthority` into `CoordinatorAgent` (remove internal routing logic)
- [ ] Add audit trail recording for routing/planning decisions
- [ ] Emit observability events at protocol boundaries (plan/route/execute)
- [ ] Update FastAPI app to create `ExecutionContext` from HTTP requests

#### Phase 4: Documentation (Week 4)
- [ ] Create migration guide (`docs/agents/MIGRATION_GUIDE.md`)
- [ ] Add API reference for protocol-compliant agents
- [ ] Create examples showing protocol usage
- [ ] Update AGENTS.md with "Protocol Adoption Status" section

### Scenario Testing (2-3 weeks)

**Goal:** End-to-end scenario tests validating orchestration with real components

**Approach:** 8 enterprise workflows with minimal mocks

- [ ] Create `tests/scenarios/` directory
- [ ] **Scenario 1:** Multi-agent dispatch (planner → coordinator → workers with memory augmentation)
- [ ] **Scenario 2:** Memory-augmented planning (RAG retrieval → plan enrichment → execution)
- [ ] **Scenario 3:** Profile-based isolation (demo vs demo_power vs production profiles)
- [ ] **Scenario 4:** Error recovery (tool failure → retry → fallback → partial success)
- [ ] **Scenario 5:** Stateful conversations (multi-turn with conversation_id continuity)
- [ ] **Scenario 6:** Complex workflows (nested orchestrations with parent_context)
- [ ] **Scenario 7:** Approval gates (budget escalation → HITL approval → continue/reject)
- [ ] **Scenario 8:** Budget enforcement (warn → escalate → block flow)

**Estimated Effort:** 8 scenarios, ~1,200 lines, 2-3 weeks

### Test Coverage Improvements (1-2 weeks)

**Goal:** Raise layer coverage from 30% → 80% (tools), 20% → 80% (memory)

#### Tools Layer Coverage (tools 30% → 80%)
- [ ] Add handler execution tests (success/failure/timeout/retry paths)
- [ ] Add budget tracking validation (cost accumulation, ceiling enforcement)
- [ ] Add parameter validation tests (all ParameterSchema cases: type/range/pattern/enum)
- [ ] Add network egress tests (SafeClient enforcement, allowlist/denylist)
- [ ] **Estimated:** 30 tests, 600 lines, 2 days

#### Memory Layer Coverage (memory 20% → 80%)
- [ ] Add profile isolation tests (no cross-profile leakage with concurrent access)
- [ ] Add retention tests (memory persistence, dirty flush on shutdown)
- [ ] Add vector backend switching tests (Chroma/Qdrant/in-memory fallback)
- [ ] Add embedding determinism tests (local fallback, no remote calls)
- [ ] **Estimated:** 25 tests, 500 lines, 2 days

---

## 🚀 v1.1 Timeline Estimate

| Phase | Work Item | Effort | Dependencies |
|-------|-----------|--------|--------------|
| Week 1 | Protocol shims | 2 days | None (start immediately) |
| Week 1 | Compliance tests | 2 days | Shims complete |
| Week 2-3 | Gradual migration | 5 days | Compliance tests passing |
| Week 2-3 | Scenario testing | 10 days | Parallel with migration |
| Week 3-4 | Coverage improvements | 4 days | Parallel with migration |
| Week 4 | Documentation | 3 days | All work complete |

**Total Estimated Effort:** 26 days (4-5 weeks with parallelization)

**Critical Path:** Protocol shims → Compliance tests → Gradual migration → Documentation

**Parallel Work:** Scenario testing and coverage improvements can happen alongside migration

---

## 🎯 Open Questions for Product Management

Before starting v1.1 work, need input on:

1. **Breaking Changes:** Is it acceptable to change agent signatures if we maintain backward compatibility wrappers?
2. **Migration Timeline:** Can we migrate calling code incrementally over multiple releases, or must it be atomic?
3. **User-Facing Benefits:** What's the user-visible value of protocol compliance? (vs internal architecture cleanup)
4. **Test Coverage Goals:** Is 80% layer coverage sufficient, or should we aim higher for critical paths?
5. **Scenario Testing Scope:** Are 8 scenarios sufficient, or should we cover more enterprise workflows?

---

## 🔧 Ongoing Maintenance & Enhancements

### Planner, Coordinator, and Tooling
- [ ] Finalize LangGraph-first planner/executor wiring with streaming callbacks
- [ ] Standardize lightweight developer checklist for planner/worker/registry changes

### Memory, RAG, and Embeddings
- [ ] Harden vector memory connectors with async batching and retention policies
- [ ] Document scoring semantics and deterministic local fallback search

### Deployment & API Profiles
- [ ] Add FastAPI LangServe-style deployment profile for hosted APIs
- [ ] Provide first-party compose profile with health checks

### Integrations & Adapters
- [ ] Build CrewAI/AutoGen adapters honoring coordinator/worker patterns
- [ ] Develop long-running planning mode inspired by Strands/Semantic Kernel

### Frontend & Workspace
- [ ] Polish frontend workspace/dashboard bundles (registry status, budgets, trace timelines)
- [ ] Ensure embedded asset pipeline stays deterministic

### Registry & Tier Enablement
- [ ] Complete Tier 1 registry composition (compose service mounts/env with health checks)
- [ ] Publish Tier 2 optional modules marked `enabled: false`
- [ ] Track watsonx credential validation and extension-aware registry parsing

## Documentation & Contributor Onboarding
- [x] Create single "System Execution Narrative" document tracing request → routing → agent → memory → response flow for contributor onboarding (completed: `docs/SYSTEM_EXECUTION_NARRATIVE.md` with CLI/FastAPI/MCP examples, complete flow diagrams, debugging tips, 20+ doc references).
- [x] Clarify FastAPI's role in architecture (transport vs orchestrator vs adapter) to prevent mixing transport and orchestration concerns (completed: `docs/architecture/FASTAPI_ROLE.md` defining FastAPI as transport layer only with clear boundaries, delegation patterns, anti-patterns, security roles, testing implications).
- [x] Document orchestrator API interface and agent lifecycle hooks explicitly with formal contract (lifecycle callbacks, failure semantics) (completed: `docs/orchestrator/README.md` - comprehensive API reference consolidating OrchestratorProtocol, lifecycle stages, failure modes, retry semantics, execution context, routing authority, integration patterns, testing requirements into single entry point).
- [x] Provide comprehensive end-to-end workflow examples for enterprise use cases (cross-system automation with error handling and HITL gates) (completed: `docs/examples/ENTERPRISE_WORKFLOWS.md` - 6 enterprise workflows with full implementations: customer onboarding with CRM/billing/approval, incident response with multi-system queries/remediation/escalation, data pipelines, invoice processing, security audits, sales qualification; includes reusable patterns, testing guidance, production checklists).
- [x] Add clear guidelines for observability, logging, tracing, and error introspection during agent execution (completed: `docs/observability/OBSERVABILITY_GUIDE.md` - comprehensive guide with structured logging, distributed tracing (OpenTelemetry/LangFuse/LangSmith), metrics collection (Prometheus/Grafana), error introspection with recovery suggestions, replayable traces for debugging, pre-built dashboards, troubleshooting playbooks for common issues).
- [x] Provide test coverage map aligned with architectural components showing which parts are tested and which aren't (completed: `docs/testing/TEST_COVERAGE_MAP.md` - comprehensive coverage map showing orchestrator 80%, agents 70%, routing 85%, failures 90%, tools 30%, memory 20%, config 0%, observability 0%; identifies critical gaps with priorities: tools security boundaries 70% gap 16h, memory data integrity 80% gap 24h, configuration precedence 100% gap 16h, observability integration 100% gap 24h; provides 3-phase testing roadmap, test fixtures inventory, CI/CD integration status).
- [x] Provide guided walkthrough for newcomers to set up and write first custom agent or extension (completed: `docs/DEVELOPER_ONBOARDING.md` - comprehensive 90-minute hands-on guide covering environment setup, first agent interaction, creating custom calculator tool with registry registration, building MathTutorAgent with lifecycle implementation, wiring components with memory + observability; includes full working examples, troubleshooting section, onboarding checklist, next steps for enhancement).
- Update inline code comments and docstrings to align with canonical contracts (OrchestratorProtocol, AgentLifecycle, ExecutionContext).
- Continue expanding example gallery with additional real-world scenarios (multi-turn conversations, RAG queries, tool composition).

## Release Engineering
- Prepare tagging and release automation aligned to `VERSION.txt` and `CHANGELOG.md` updates.
- Keep migration notes current for any breaking changes across MCP runners, registry behaviors, or sandbox policies.
- [ ] Flesh out Watsonx provider, Langflow export/import, and sandbox hardening
