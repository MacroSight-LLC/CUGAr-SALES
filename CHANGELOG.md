
# 📦 CHANGELOG

All notable changes to the CUGAR Agent project will be documented in this file.

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

### ⚠️ Known Gaps
- CLI runner may need test scaffolding
- Tool schema validation needs stronger contract enforcement
- Logging verbosity defaults may need hardening

---

## [vNext]
- In development: GitHub Actions CI, coverage reports, Langflow project inspector

---
