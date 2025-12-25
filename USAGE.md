# Usage Guide

This guide covers the fastest way to configure and run the CUGA agent from source. For deeper architecture notes, see the docs under `docs/`.

## Prerequisites
- Python 3.12 (uv manages virtualenv creation automatically)
- Node/Playwright dependencies for browser automation (`uv run playwright install --with-deps chromium`)
- Access to an LLM provider (OpenAI, Azure OpenAI, WatsonX, LiteLLM, or OpenRouter)

## Install
```bash
uv sync --all-extras --dev
uv run playwright install --with-deps chromium
```

## Configure a model profile
The agent loads settings from `./src/cuga/settings.toml` by default. To use a provider-specific profile, set `AGENT_SETTING_CONFIG` to any file in `./configurations/models`, for example:

```bash
export AGENT_SETTING_CONFIG=settings.openai.toml
export OPENAI_API_KEY=sk-...
```

Demo profiles are intentionally low-permission. For production deployments, review `docs/SECURITY.md` and keep secrets in your shell or `.env.mcp` (never commit them).

## Run common services
The Typer CLI exposes the main entrypoints. The examples below use the local sandbox. Add `--sandbox` to enable the remote sandbox group.

```bash
# Start registry + demo agent (ports 8001 and 7860)
uv run cuga start demo

# Start only the registry API on port 8001
uv run cuga start registry

# Start CRM demo (email MCP + CRM API)
uv run cuga start demo_crm --sample-memory-data

# Start memory or AppWorld helpers
uv run cuga start memory
uv run cuga start appworld
```

Check service status or stop everything when you are done:

```bash
uv run cuga status
uv run cuga stop demo
```

## Registry and MCP tips
- Registries live under `config/` and `registry.yaml`. Use `uv run registry` scripts from `scripts/` to inspect entries.
- MCP servers are sandboxed; update paths and ports in `configurations/` rather than hard-coding them.
- Run `python scripts/verify_guardrails.py` before shipping changes to confirm registry merge and guardrail routing.

## Troubleshooting
- Ensure ports 7860, 8000, 8001, 8888, and 9000 are free before starting demos (the CLI will attempt to clean up listeners).
- If Playwright browsers are missing, rerun `uv run playwright install --with-deps chromium`.
- Use `--verbose` with any `cuga` command for detailed logs.
