# 🧠 Agents & Orchestration Guide

This document is the **primary entrypoint for contributors, Codex/LLM agents, and maintainers** working on the CUGAR agent framework.  
It defines **guardrails**, explains the **controller → planner → executor** pipeline, and maps the documentation surface area.

---

## 🚦 Universal Guardrails (Apply Everywhere)

These rules are non‑negotiable and apply to all code paths, tools, and subagents:

- 🔒 **Subagent Isolation**
  - No shared mutable state between profiles
  - No tool leakage across sandbox boundaries

- 🔐 **Secrets Handling**
  - API keys must be non‑empty (see Langflow production guard)
  - Secrets must never be logged, printed, or returned in outputs

- ✅ **Determinism First**
  - Prefer predictable, minimal changes
  - Avoid implicit side effects
  - Always accompany behavior changes with tests and documentation

- 🧩 **Registry Hygiene**
  - Registry fragments must resolve relative to their profile file
  - Conflicts must fail fast and loudly
  - Silent merges are forbidden

---

## 🧭 Architecture Overview

CUGAR follows a **strictly layered agent pipeline**. Each layer has a single responsibility and operates within a **profile‑scoped sandbox**.

| Component     | Source Path                         | Responsibility |
|--------------|-------------------------------------|----------------|
| **Controller** | `src/cuga/agents/controller.py` | Owns orchestration. Validates inputs, creates sandboxed registries, and coordinates planning and execution. |
| **Planner** | `src/cuga/agents/planner.py` | Translates a goal into an ordered list of `PlanStep` objects based on available tools. |
| **Executor** | `src/cuga/agents/executor.py` | Executes `PlanStep`s using profile‑scoped tools and returns structured results. |
| **Registry** | `src/cuga/agents/registry.py` | Loads, isolates, and merges tool metadata per profile. Enforces conflict‑free composition. |

---

## 🔄 Message Flow

The following diagram represents the canonical execution path for all agents.

```

plantuml
@startuml
actor User
participant Controller
participant Planner
participant Executor
participant "Tool Registry" as Registry

User -> Controller: goal + profile
Controller -> Registry: sandbox(profile)
Controller -> Planner: plan(goal, sandboxed registry)
Planner --> Controller: PlanStep list
Controller -> Executor: execute_plan(plan, sandboxed registry, context)
Executor -> Registry: resolve(tool)
Executor --> Controller: ExecutionResult
Controller --> User: output + step log
@enduml

```

---

## 📁 Profiles & Registry Generation

Profiles define **what an agent can do**. They live under:

```

configurations/profiles/

```

### Key Rules

* Registry fragments are resolved **relative to the profile file**
* Fragment conflicts fail fast with explicit file references
* Legacy fragment behavior is deprecated and documented

### Langflow Production Projects

Profiles may define templated Langflow projects using:

```

[profiles.<name>.langflow_prod_projects]

````

Refer to `docs/registry_merge.md` for:

* Conflict semantics
* Template expansion
* Deprecation notices
* Debugging guidance

### Useful Commands

```bash
make profile-demo_power
````

Generates:

```
build/mcp_servers.demo_power.yaml
```

To export MCP servers for tooling:

```bash
eval $(make env-dev)
# or
set -a; source .env.mcp; set +a
```

---

## 🗺️ Documentation Map

| File                      | Purpose                                                          |
| ------------------------- | ---------------------------------------------------------------- |
| `README.md`               | Project overview, quickstart, and environment setup              |
| `AGENTS.md`               | (This file) Architecture, guardrails, and contributor entrypoint |
| `docs/agent-core.md`      | Deep dive into the agent lifecycle and pipeline                  |
| `docs/tools.md`           | Tool interfaces, scopes, and registration contracts              |
| `docs/mcp_integration.md` | MCP protocol usage and integration patterns                      |
| `docs/registry_merge.md`  | Registry assembly, conflict resolution, and templating           |
| `docs/Security.md`        | Security expectations and secret‑handling policies               |
| `docs/embedded_assets.md` | Embedded asset compression, runtime behavior, and deployment     |

---

## 🛠️ Troubleshooting

| Issue                                   | Resolution                                                                |
| --------------------------------------- | ------------------------------------------------------------------------- |
| Duplicate `mcpServers` or service names | Remove or rename the conflicting fragment. Errors list both source files. |
| YAML parse errors                       | Fix the file and line referenced in the error output.                     |
| Incorrect profile paths                 | Ensure all fragments are relative to the profile file location.           |
| Missing tools at runtime                | Verify registry merge output and sandbox scope.                           |

---

## 🧱 Contributor Expectations

* Changes must preserve **profile isolation**
* New tools require:

  * Clear interfaces
  * Registry documentation
  * Tests
* Behavioral changes must:

  * Be deterministic
  * Be documented
  * Include test coverage

When in doubt, prefer **explicit structure over implicit magic**.

---

## 🏁 Next Reading

* `docs/agent-core.md` — full pipeline and lifecycle
* `docs/tools.md` — tool authoring and execution
* `docs/Security.md` — production hardening requirements

This document defines the contract.
If your change violates it, the change is wrong.

---

## 🧾 Commit Hygiene & CHANGELOG Rules

> ✅ All contributors — human or automated — must follow the versioning and changelog discipline below.

### 🔢 Semantic Versioning

We follow [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

* `MAJOR` – breaking changes to registry format, agent pipeline, or CLI usage
* `MINOR` – new features, tools, modules, or interfaces
* `PATCH` – bugfixes, documentation, tests, or refactors

The current version lives in:

```
/VERSION.txt
```

### 📝 CHANGELOG.md Updates (MANDATORY)

For **every pull request or Codex auto-commit**, update `/CHANGELOG.md` under the correct version section:

* ➕ **Added**: new modules, config keys, registry logic
* 🔁 **Changed**: structure, default behavior, tool interfaces
* 🐞 **Fixed**: bugs, parsing errors, test logic
* 🧼 **Removed**: deprecated logic, legacy fragments

Use clear bullet points. Prefix each entry with an emoji (`➕`, `🔁`, `🐞`, etc) and avoid vague labels.

### 🔁 Commit Format (Codex-Friendly)

To ensure consistent version bumping by Codex agents, every commit must include:

```
[vX.Y.Z] {CHANGE_TYPE}: {SUMMARY}
```

✅ Example:

```
[v1.0.1] 🔁 Changed: registry now merges fragments using new path resolver
[v1.1.0] ➕ Added: memory replay module + Langflow fallback handler
```

This allows Codex to:

* Auto-tag releases
* Generate release notes
* Validate changelog parity with commits

---

📌 If you’re unsure: default to `PATCH`, and include a note in the changelog under `🔁 Changed`.
