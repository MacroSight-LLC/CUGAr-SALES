# CUGAR Agent (2025 Edition)

[![CI](https://github.com/TylrDn/cugar-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/TylrDn/cugar-agent/actions/workflows/ci.yml)
[![Tests](https://github.com/TylrDn/cugar-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/TylrDn/cugar-agent/actions/workflows/tests.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-pytest--cov-success)](./TESTING.md)

CUGAR Agent is a production-grade, modular agent stack that embraces 2025’s best practices for LangGraph/LangChain orchestration, LlamaIndex-powered RAG, CrewAI/AutoGen-style multi-agent patterns, and modern observability (Langfuse/OpenInference/Traceloop). The repository is optimized for rapid setup, reproducible demos, and safe extension into enterprise environments.
Policy and change-management guardrails are maintained in [AGENTS.md](AGENTS.md) and must be reviewed before modifying agents or tools.

## At a Glance
- **Composable agent graph**: Planner → Tool/User executor → Memory+Observability hooks, wired for LangGraph.
- **RAG-ready**: LlamaIndex loader/retriever scaffolding with pluggable vector stores (Chroma, Qdrant, Weaviate, Milvus).
- **Multi-agent**: CrewAI/AutoGen-compatible patterns and coordination helpers.
- **Observability-first**: Langfuse/OpenInference emitters, structured audit logs, profile-aware sandboxing.
- **Developer experience**: Typer CLI, Makefile tasks, uv-based env management, Ruff/Black/isort + mypy, pytest+coverage, pre-commit.
- **Deployment**: Dockerfile, GitHub Actions CI/CD, sample configs and .env.example for cloud/on-prem setups.

## Recent updates (scaffolding)

- Added Watsonx Granite provider stub with deterministic defaults and JSONL audit trail to simplify enterprise alignment.
- Added Langflow component placeholders (planner, executor, guard, Granite LLM) to prep for flow export/import commands.
- Added registry validation, sandbox profile starter, and documentation shells for security and guardrail mapping.

## Architecture
```
                       ┌──────────────────────────┐
                       │        Controller        │
                       │ (policy + correlation ID)│
                       └────────────┬─────────────┘
                                    │
                           plan(goal, registry)
                                    │
┌──────────────┐          ┌─────────▼─────────┐          ┌────────────────────┐
│ Registry/CFG │──sandbox▶│    Planner        │──steps──▶│   Executor/Tools   │
│ (Hydra/Dyn)  │          │ (ReAct/Plan&Exec) │          │ (LCEL, MCP, HTTP)  │
└──────────────┘          └─────────┬─────────┘          └─────────┬──────────┘
                                    │                              │
                          traces + memory writes         Langfuse/OpenInference
                                    │                              │
                            ┌───────▼────────┐                   ┌─▼────────┐
                            │ Memory / RAG   │◀────context───────│  Clients │
                            │ (LlamaIndex)   │                   │ (CLI/API)│
                            └────────────────┘                   └──────────┘
```

For a role-by-role, mode-aware walkthrough of how the controller, planners, executors, and MCP tool packs fit together (plus configuration keys), see [docs/agents/architecture.md](docs/agents/architecture.md). For an MCP + LangChain web stack overview that covers the FastAPI backend, Vue 3 frontend, streaming flows, and configuration surfaces, see [docs/MCP_LANGCHAIN_OVERVIEW.md](docs/MCP_LANGCHAIN_OVERVIEW.md). A step-by-step stable local launch checklist (registry + sandbox + Langflow readiness) lives in [docs/local_stable_launch.md](docs/local_stable_launch.md).

## Documentation

📘 **[System Execution Narrative](docs/SYSTEM_EXECUTION_NARRATIVE.md)** - Complete request → response flow for contributor onboarding (3 entry points: CLI/FastAPI/MCP, 8 execution phases with security boundaries, observability integration, debugging tips, testing guidance)

🔧 **[FastAPI Role Clarification](docs/architecture/FASTAPI_ROLE.md)** - Defines FastAPI as transport layer only (HTTP/SSE, auth, budget enforcement) vs orchestration (planning, coordination, execution) to prevent mixing concerns

⚙️ **[Orchestrator Interface and Semantics](docs/orchestrator/README.md)** - Formal specification for orchestrator API with lifecycle callbacks, failure taxonomy, retry semantics, execution context, routing authority, and implementation patterns

🏢 **[Enterprise Workflow Examples](docs/examples/ENTERPRISE_WORKFLOWS.md)** - Comprehensive end-to-end workflow examples for typical enterprise use cases (customer onboarding, incident response, data pipelines) with planning, error recovery, HITL gates, and external API automation

📊 **[Observability and Debugging Guide](docs/observability/OBSERVABILITY_GUIDE.md)** - Comprehensive instrumentation guide with structured logging, distributed tracing (OpenTelemetry/LangFuse/LangSmith), metrics collection, error introspection, replayable traces, dashboards, and troubleshooting playbooks

🧪 **[Test Coverage Map](docs/testing/TEST_COVERAGE_MAP.md)** - Comprehensive test coverage aligned with architectural components showing what's tested (orchestrator 80%, routing 85%, failures 90%) and critical gaps (tools 30%, memory 20%, config 0%, observability 0%) with priorities for additional testing

👋 **[Developer Onboarding Guide](docs/DEVELOPER_ONBOARDING.md)** - Step-by-step walkthrough for newcomers: environment setup (15 min), first agent interaction (10 min), create custom tool (20 min), build custom agent (30 min), wire components together (15 min) with full working examples (calculator tool, math tutor agent, tutoring workflow)

## Quickstart
```bash
# 1) Install (Python >=3.10)
uv sync --all-extras --dev
uv run playwright install --with-deps chromium

# 2) Configure environment
cp .env.example .env
# set OPENAI_API_KEY / LANGFUSE_SECRET / etc inside .env

# 3) Run demo agent locally
uv run cuga start demo

# 4) Try modular stack example
uv run python examples/run_langgraph_demo.py --goal "triage a support ticket"
```

## Installation
- **Dependencies**: `uv` (or `pip`), optional browsers for Playwright, optional vector DB service (Chroma/Weaviate/Qdrant/Milvus).
- **Development**: `uv sync --all-extras --dev` installs dev + optional extras (`memory`, `sandbox`, `groq`, etc.).
- **Pre-commit**: `uv run pre-commit install` then `uv run pre-commit run --all-files`.

## Configuration
- `.env.example` lists required variables for LLMs, tracing, and storage.
- `configs/` holds YAML/TOML profiles for agents, LangGraph graphs, memory backends, and observability.
- `registry.yaml` and `config/` house MCP/registry defaults; use `scripts/verify_guardrails.py` before shipping changes.

## Guardrails & Change Management
- Review [AGENTS.md](AGENTS.md) before altering planners, tools, or registry entries; it is the single source of truth for allowlists, sandbox expectations, budgets, and redaction.
- Guardrail and registry changes are enforced by CI: `scripts/verify_guardrails.py --base <branch>` collects diffs and fails if `README.md`, `PRODUCTION_READINESS.md`, `CHANGELOG.md`, or `todo1.md` are not updated alongside guardrail changes or if `## vNext` lacks a guardrail note.
- Keep production checklists ([PRODUCTION_READINESS.md](PRODUCTION_READINESS.md)) and security docs in sync with guardrail adjustments so downstream users understand the default policies and where to override them.
- Developer checklist: ensure registry entries declare sandboxes + `/workdir` pinning for exec scopes, budget/observability env keys (`AGENT_*`, `OTEL_*`, LangFuse/LangSmith, Traceloop) are wired, `docs/mcp/tiers.md` is regenerated from `docs/mcp/registry.yaml`, and new/updated tests exercise planner ranking, import guardrails, and registry hot-swap determinism.

## Agent Types
- **Planner**: ReAct or Plan-and-Execute; emits steps with policy-aware cost/latency hints.
- **Tool Executor**: LCEL/LangChain tools, MCP adapters, HTTP/OpenAPI runners with sandboxed registry resolution.
- **RAG/Data Agent**: LlamaIndex loader+retriever (docs in `rag/`), vector memory connectors in `memory/`.
- **Coordinator**: CrewAI/AutoGen-like orchestrator for multi-agent hand-offs.
- **Observer**: Langfuse/OpenInference emitters with correlation IDs and redaction hooks.

See `AGENTS.md` for role details and `USAGE.md` for end-to-end flows.

## RAG Setup
- Drop documents into `rag/sources/` or configure a remote store.
- Choose a backend in `configs/memory.yaml` (chroma|qdrant|weaviate|milvus|local).
- Run `uv run python scripts/load_corpus.py --source rag/sources --backend chroma`.
- Query via `uv run python examples/rag_query.py --query "How do I add a new MCP tool?"`.

## Memory & State
- `memory/` exposes `VectorMemory` (in-memory fallback), summarization hooks, and profile-scoped stores.
- State keys are namespaced by profile to preserve sandbox isolation.
- Persistence is opt-in; see `configs/memory.yaml` and `TESTING.md` for guidance.

## Observability
- Langfuse client is wired via `observability/langfuse.py` with sampling + PII redaction hooks.
- OpenInference/Traceloop emitters are optional and can be toggled per profile.
- Structured audit logs live under `logs/` when enabled; avoid committing artifacts.
- Watsonx Granite calls validate credentials up front and append JSONL audit rows with timestamp, actor, parameters, and outcome for offline review.

## Multi-Agent & Coordination
- `agents/` outlines planner/worker/tool-user patterns and how to register them with CrewAI/AutoGen.
- `examples/multi_agent_dispatch.py` demonstrates round-robin delegation with shared vector context.
- Hand-offs carry correlation IDs and redacted summaries, not raw prompts.

## Testing & Quality Gates
- Run `make lint test typecheck` locally.
- Pytest with coverage is configured (see `TESTING.md`).
- CI (GitHub Actions) runs lint, type-check, tests, and guardrail verification on pushes/PRs.

## Security & Safe Execution

CUGAR Agent enforces security-first design with deny-by-default policies per [AGENTS.md](AGENTS.md) § 4 Sandbox Expectations:

### MCP & OpenAPI Governance

- **Policy Gates**: HITL approval points for WRITE/DELETE/FINANCIAL actions (Slack send, file delete, stock orders)
- **Per-Tenant Capability Maps**: 8 organizational roles (marketing/trading/engineering/support) with tool allowlists/denylists
- **Runtime Health Checks**: Tool discovery ping, schema drift detection, cache TTLs to prevent huge cold-start lists
- **Layered Access Control**: Tool registration → Tenant map → Tool-level restrictions → Rate limits

See [docs/security/GOVERNANCE.md](docs/security/GOVERNANCE.md) for complete governance architecture, configuration files, and integration patterns.

### Eval/Exec Elimination
- **No eval/exec**: All `eval()` and `exec()` calls eliminated from production code paths
- **AST-based expression evaluation**: Use `safe_eval_expression()` from `cuga.backend.tools_env.code_sandbox.safe_eval` for mathematical expressions
  - Allowlisted operators: Add/Sub/Mul/Div/FloorDiv/Mod/Pow
  - Allowlisted functions: math.sin/cos/tan/sqrt/log/exp, abs/round/min/max/sum
  - Denies: assignments, imports, attribute access, eval/exec/__import__
- **SafeCodeExecutor**: All code execution routed through `SafeCodeExecutor` or `safe_execute_code()` from `cuga.backend.tools_env.code_sandbox.safe_exec`
  - Import allowlist: Only `cuga.modular.tools.*` permitted
  - Import denylist: os/sys/subprocess/socket/pickle/eval/exec/compile
  - Restricted builtins: Safe operations (math/types/iteration) allowed; eval/exec/open/__import__ denied
  - Filesystem deny-default: No file operations unless explicitly allowed
  - Timeout enforcement: 30s default, configurable
  - Audit trail: All imports/executions logged with trace_id

### HTTP & Secrets Hardening
- **SafeClient wrapper**: All HTTP requests MUST use `SafeClient` from `cuga.security.http_client`
  - Enforced timeouts: 10.0s read, 5.0s connect, 10.0s write, 10.0s total
  - Automatic retry: Exponential backoff (4 attempts max, 8s max wait)
  - URL redaction: Query params and credentials stripped from logs
- **Env-only secrets**: Credentials MUST be loaded from environment variables
  - CI enforces `.env.example` parity validation (no missing keys)
  - Secret scanning: trufflehog + gitleaks on every push/PR
  - Hardcoded API keys/tokens trigger CI failure

### Import & Sandbox Controls
- **Import restrictions**: Dynamic imports limited to `cuga.modular.tools.*` namespace only
- **Profile isolation**: Memory and tool access namespaced per profile; no cross-profile leakage
- **Sandbox profiles**: All registry entries declare sandbox profile (py/node slim|full, orchestrator)
- **Read-only defaults**: Mounts are read-only by default; `/workdir` pinning for exec scopes

See [AGENTS.md](AGENTS.md) for complete guardrail specifications and [docs/security/](docs/security/) for detailed security controls.

## FAQ
- **Which LLMs are supported?** 
  - OpenAI (GPT-4o, GPT-4 Turbo)
  - Azure OpenAI
  - Anthropic (Claude 3.5 Sonnet, Opus, Haiku)
  - **IBM Watsonx / Granite 4.0** (granite-4-h-small, granite-4-h-micro, granite-4-h-tiny) — **Default provider** with deterministic temperature=0.0
  - Groq (Mixtral)
  - Google GenAI
  - Any LangChain-compatible model via adapters
- **Do I need a vector DB?** Not for quickstarts; an in-memory store is bundled. For production use Chroma/Qdrant/Weaviate/Milvus.
- **How do I add a new tool?** Implement `ToolSpec` in `tools/registry.py` or wrap an MCP server; see `USAGE.md`.
- **Is this production-ready?** Core stack follows sandboxed, profile-scoped design with observability. Harden configs before internet-facing use.
- **How do I configure Watsonx/Granite?** Set environment variables: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, and optionally `WATSONX_URL`. See `docs/configuration/ENVIRONMENT_MODES.md` for details.

## Documentation

For a complete understanding of system execution flow:
- 📘 **[System Execution Narrative](docs/SYSTEM_EXECUTION_NARRATIVE.md)** - Complete request → response flow for contributor onboarding (CLI/FastAPI/MCP modes, routing, agents, memory, tools)
- 🏗️ [Architecture](ARCHITECTURE.md) - High-level design overview
- 🚀 [Quick Start](QUICK_START.md) - Get up and running quickly
- 🤝 [Contributing](CONTRIBUTING.md) - How to contribute to the project
- 🔒 [Production Readiness](PRODUCTION_READINESS.md) - Deployment considerations

## Roadmap Highlights
- Streaming-first ReAct policies with beta support for Strands/semantic state machines.
- Built-in eval harness for self-play and regression suites.
- Optional LangServe or FastAPI hosting for SaaS-style deployments (see `ROADMAP.md`).

## License
Apache 2.0. See [LICENSE](LICENSE).
