# Security Policy

CUGA is designed for sandboxed experimentation. The examples and demo settings are not production hardened. Please keep secrets and customer data out of the repository and demo flows.

## Reporting a Vulnerability
- Email: [security@cuga.dev](mailto:security@cuga.dev)
- Please include a detailed description, reproduction steps, and any logs available.
- Avoid sharing secrets or customer data in reports. If sensitive artifacts are required, request a secure channel in your first message.

## Supported Versions
Security fixes target the `main` branch. Release tags receive fixes on a best-effort basis. If you rely on a previous release, please mention the tag in your report so we can triage impact.

## Safe Handling Guidelines
- Run agents and MCP servers in sandboxed environments with locked-down network access whenever possible.
- Rotate API keys frequently and configure them through environment variables or `.env.mcp`, never hard-code secrets.
- Use the guardrail verification script (`python scripts/verify_guardrails.py`) to confirm routing markers and registry hygiene before shipping changes.
