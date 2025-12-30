"""Tool registry with schema validation and simple rate-limit placeholders."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    from jsonschema import Draft7Validator
except Exception:  # pragma: no cover - fallback when dependency missing
    Draft7Validator = None  # type: ignore

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


@dataclass
class RegistryServer:
    id: str
    url: str
    enabled: bool = True
    rate_limit_per_minute: int = 60


class ToolRegistry:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> List[RegistryServer]:
        payload = json.loads(self.path.read_text()) if self.path.suffix == ".json" else json.loads(json.dumps({}))
        if not payload:
            try:
                import yaml

                payload = yaml.safe_load(self.path.read_text())
            except Exception:
                payload = {}
        if Draft7Validator:
            Draft7Validator(_SCHEMA).validate(payload)
        servers = []
        for raw in payload.get("servers", []):
            servers.append(
                RegistryServer(
                    id=raw["id"],
                    url=raw["url"],
                    enabled=raw.get("enabled", True),
                    rate_limit_per_minute=raw.get("rate_limit_per_minute", 60),
                )
            )
        return servers

    def enabled(self) -> Iterable[RegistryServer]:
        return [s for s in self.data if s.enabled]
