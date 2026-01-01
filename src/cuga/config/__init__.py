"""
Configuration Resolution Package

Provides unified configuration resolution with explicit precedence layers,
provenance tracking, and environment validation.

Canonical precedence order (highest to lowest):
    1. CLI arguments
    2. Environment variables
    3. .env files (.env.mcp, .env, .env.example)
    4. YAML configs (configs/*.yaml, config/registry.yaml)
    5. TOML configs (settings.toml, eval_config.toml)
    6. Configuration defaults (configurations/_shared/*.yaml)
    7. Hardcoded defaults (in code)

See docs/configuration/CONFIG_RESOLUTION.md for complete specification.
"""

from .resolver import ConfigResolver, ConfigLayer, ConfigValue, ConfigSource
from .validators import (
    validate_environment_mode,
    EnvironmentMode,
    ValidationResult,
    ConfigValidator,
)

__all__ = [
    "ConfigResolver",
    "ConfigLayer",
    "ConfigValue",
    "ConfigSource",
    "validate_environment_mode",
    "EnvironmentMode",
    "ValidationResult",
    "ConfigValidator",
]
