from __future__ import annotations

import logging
from typing import Any, Dict, List

_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "servers": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "url"],
                "properties": {
                    "id": {"type": "string"},
                    "url": {"type": "string"},
                    "enabled": {"type": "boolean"},
                    "rate_limit_per_minute": {"type": "integer", "minimum": 1},
                },
            },
        }
    },
}


def validate_registry_payload(payload: Dict[str, Any], validator: Any, logger: logging.Logger | None = None) -> List[Dict[str, Any]]:
    """Validate registry payload using Draft7 with defensive fallbacks."""

    logger = logger or logging.getLogger(__name__)
    servers = payload.get("servers", [])
    if not isinstance(servers, list):
        logger.warning(
            "registry_schema_invalid",
            extra={"event": "registry_schema_invalid", "reason": "servers_not_list"},
        )
        return []

    if validator:
        try:
            errors = list(validator.iter_errors(payload))
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.error(
                "registry_schema_validation_error",
                extra={"event": "registry_schema_validation_error", "error": str(exc)},
            )
            return []

        for err in errors:
            logger.warning(
                "registry_schema_violation",
                extra={
                    "event": "registry_schema_violation",
                    "message": err.message,
                    "path": list(err.path),
                    "schema_path": list(err.schema_path),
                },
            )

    filtered: List[Dict[str, Any]] = []
    for idx, raw in enumerate(servers):
        if not isinstance(raw, dict):
            logger.warning(
                "registry_entry_invalid_type",
                extra={"event": "registry_entry_invalid_type", "index": idx},
            )
            continue
        if not raw.get("id") or not raw.get("url"):
            logger.warning(
                "registry_entry_missing_fields",
                extra={"event": "registry_entry_missing_fields", "index": idx},
            )
            continue
        filtered.append(raw)

    return filtered
