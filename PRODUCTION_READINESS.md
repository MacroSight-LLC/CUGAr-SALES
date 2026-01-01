# ✅ Production Readiness Checklist – v1.0.0

This checklist ensures the CUGAR Agent system is hardened, documented, and version-controlled for production release.

---

## 📁 Repository Structure

- [x] `/src/` has modular structure (`agents`, `mcp`, `tools`, `config`)
- [x] `/docs/` contains architecture, security, integration, and tooling references
- [x] `/config/` stores Hydra-composed registry defaults and fragment overrides with inheritance markers
- [x] `/tests/` directory exists with core coverage
- [x] `/examples/` directory demonstrates agent usage

---

## 🔐 Security & Secrets

- [x] `.env.example` included and redacted
- [x] `USE_EMBEDDED_ASSETS` feature flag documented
- [x] Watsonx Granite provider validates env-based credentials (`WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`) with deterministic defaults and audit logging.
- [x] No hardcoded keys or tokens
- [x] Secrets validated before use (`assert key`)
- [x] `detect-secrets` baseline committed
- [x] `SECURITY.md` defines CI & runtime rules
- [x] **HTTP Client Hardening**: All HTTP requests use `SafeClient` wrapper with enforced timeouts (10.0s), automatic retry (4 attempts, exponential backoff), and URL redaction in logs. No raw httpx/requests/urllib usage.
- [x] **Secrets Management**: Env-only credential enforcement via `cuga.security.secrets` module. `.env.example` parity validated in CI (no missing keys). `SECRET_SCANNER=on` runs trufflehog + gitleaks on every push/PR. Hardcoded API keys/tokens/passwords trigger CI failure.
- [x] **Mode-Specific Validation**: Startup validation enforces required env vars per mode: LOCAL (model API key), SERVICE (AGENT_TOKEN + budget + model key), MCP (servers file + profile + model key), TEST (no requirements).

---

## 📦 Build & Distribution

- [x] `Makefile` and `Dockerfile` tested
- [x] `uv` workflows for stability & asset builds
- [x] Embedded asset pipeline (`build_embedded.py`) verified
- [x] Compression ratios documented

---

## 🔍 Documentation Map

- [x] `AGENTS.md` – entrypoint for all contributors
- [x] `AGENT-CORE.md` – agent lifecycle, pipeline
- [x] `TOOLS.md` – structure, schema, usage
- [x] `MCP_INTEGRATION.md` – tool bus and lifecycle
- [x] `REGISTRY_MERGE.md` – Hydra-based registry fragment handling and enablement rules
- [x] `SECURITY.md` – production secret handling
- [x] `EMBEDDED_ASSETS.md` – compression and distribution

---

## 🛡️ Guardrails & Registry

- [x] Registry entries declare sandbox profile (`py/node slim|full`, `orchestrator`) with `/workdir` pinning for exec scopes and read-only defaults.
- [x] Budget and observability env keys (`AGENT_*`, `OTEL_*`, `LANGFUSE_*`, `OPENINFERENCE_*`, `TRACELOOP_*`) wired with default `warn` budget policy and ceiling/escalation caps.
- [x] `docs/mcp/registry.yaml` kept in sync with generated `docs/mcp/tiers.md`; hot-swap reload path tested and deterministic ordering verified.
- [x] Guardrail updates accompanied by README/CHANGELOG/todo1 updates and `scripts/verify_guardrails.py --base <ref>` runs.

---

## 🧪 Tests & Stability

- [x] Core modules tested (`controller`, `planner`, `executor`)
- [x] `run_stability_tests.py` executed cleanly
- [ ] Functional test coverage ≥ 80% (📍 target)
- [x] Lint passes (`ruff`, `pre-commit`, CI)
- [x] Legacy agent versions isolated or removed

---

## 🏷️ Versioning

- [x] `VERSION.txt` present → `1.0.0`
- [x] `CHANGELOG.md` documents all v1.0.0 features
- [x] Git tag proposed:
  ```bash
  git tag -a v1.0.0 -m "Initial production release"
  git push origin v1.0.0
