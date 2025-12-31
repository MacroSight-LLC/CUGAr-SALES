# Architecture Overview

> **For a narrative walkthrough of the complete execution flow**, see [`docs/SYSTEM_EXECUTION_NARRATIVE.md`](docs/SYSTEM_EXECUTION_NARRATIVE.md) - traces request → response with CLI/FastAPI/MCP examples, routing decisions, agent lifecycle, memory operations, and tool execution.
>
> **For FastAPI's specific role**, see [`docs/architecture/FASTAPI_ROLE.md`](docs/architecture/FASTAPI_ROLE.md) - clarifies FastAPI as transport layer only (not orchestrator) to prevent mixing transport and orchestration concerns.

## Modular Stack
- Planner → Coordinator → Workers with profile-scoped VectorMemory.
- Embeddings: deterministic hashing embedder; vector backends (FAISS/Chroma/Qdrant) behind `VectorBackend` protocol.
- RAG: RagLoader validates backends at init and persists `path`/`profile` metadata; RagRetriever surfaces scored hits.

## Scheduling & Execution
- PlannerAgent ranks tools by goal similarity (ReAct/Plan-and-Execute hybrid) respecting config max steps.
- CoordinatorAgent dispatches workers via thread-safe round-robin to guarantee fairness.
- WorkerAgent defaults profile to memory profile, propagates `trace_id`, and logs structured traces.

## Tooling & CLI
- ToolRegistry restricts dynamic imports to `cuga.modular.tools.*`.
- CLI (`python -m cuga.modular.cli`) provides `ingest`, `query`, `plan` with JSON logs and shared state file for demos.

For a mode-aware, controller → planner → executor narrative (including MCP pack assembly and configuration keys), see [docs/agents/architecture.md](docs/agents/architecture.md).
