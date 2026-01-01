"""
Security module for CUGAR Agent.

Provides:
- SafeClient: HTTP client with enforced timeouts and retry logic
- AsyncSafeClient: Async variant of SafeClient
- Secrets management: env-only enforcement and validation
- URL/secret redaction for safe logging

Per AGENTS.md canonical requirements.
"""

from cuga.security.http_client import (
    SafeClient,
    AsyncSafeClient,
    DEFAULT_TIMEOUT,
)

from cuga.security.secrets import (
    is_sensitive_key,
    redact_dict,
    validate_env_parity,
    enforce_env_only_secrets,
    detect_hardcoded_secrets,
    validate_startup_env,
)

__all__ = [
    # HTTP client
    "SafeClient",
    "AsyncSafeClient",
    "DEFAULT_TIMEOUT",
    # Secrets management
    "is_sensitive_key",
    "redact_dict",
    "validate_env_parity",
    "enforce_env_only_secrets",
    "detect_hardcoded_secrets",
    "validate_startup_env",
]
