from __future__ import annotations

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
