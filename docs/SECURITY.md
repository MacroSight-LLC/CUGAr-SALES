
# 🔐 Security & Secrets Policy

This document defines the security model, secrets handling practices, and production hardening expectations for the CUGAR agent framework.

---

## 🚧 Key Principles

- **Fail Closed**: All security checks should default to denying access unless explicitly allowed.
- **No Secrets in Logs**: Secrets must never be printed, logged, or returned in structured outputs.
- **Immutable Inputs**: Secrets or tokens passed to tools must be treated as read-only.
- **Separation of Concerns**: Secret access is handled by the config loader, not the tools.

---

## 🔑 Secrets Management

All secrets (API keys, tokens, credentials) must be:

- Stored in `.env` or `.env.{envname}` files (never hardcoded)
- Loaded via a centralized config loader (e.g. `cuga.config`)
- Validated as **non-empty** before use

**Example:**

```env
OPENAI_API_KEY=sk-xxx
MCP_TOKEN=prod-abc123
```

**NEVER:**

```python
openai.api_key = "sk-hardcoded-key"  # ❌ BAD
```

---

## ✅ Validation Rules

Secrets must be validated early, e.g.:

```python
assert config.OPENAI_API_KEY, "Missing OpenAI key"
```

Secrets should be passed to tools via **injected config**, not global access.

---

## 🧼 Secret Sanitization in Logs

Tools and agents must:

- Mask or remove any keys, tokens, or passwords from logs
- Use redaction helpers when logging config or tool state

**Safe Logging Example:**

```python
log.info(f"Loaded config for tool: {tool.name}, key=***REDACTED***")
```

---

## 🔒 Production Guardrails

When `ENV=production`:

- Disable verbose logging (no stack traces by default)
- Disable dynamic eval or LLM-driven tool access
- Harden all profile-based tool loading (no wildcard registries)
- Enforce secrets presence via startup check

---

## 🧪 Security in CI

### Pre-commit Hooks:

Use `.secrets.baseline` and `detect-secrets` plugin to detect leaks before commit.

```bash
pre-commit run detect-secrets --all-files
```

### GitHub Actions:

Ensure `.env` files are not committed. Block PRs if `.env` is modified.

---

## 📘 Related Docs

- `AGENTS.md` – contributor guardrails
- `TOOLS.md` – how tools consume secrets safely
- `REGISTRY_MERGE.md` – sanitization of fragments with embedded tokens

---

🔁 Return to [Agents.md](../AGENTS.md)
