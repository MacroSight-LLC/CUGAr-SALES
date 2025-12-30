"""Tool registry with schema validation and extension-aware loading."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

_jsonschema_spec = importlib.util.find_spec("jsonschema")
if _jsonschema_spec:
    from jsonschema import Draft7Validator  # type: ignore
else:  # pragma: no cover
    Draft7Validator = None  # type: ignore

from .models import RegistryServer
from .schema import _SCHEMA


class RegistryLoader:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _load(self) -> List[RegistryServer]:
        payload: Dict[str, Any] = {}

        if self.path.exists():
            content = self.path.read_text(encoding="utf-8")
            suffix = self.path.suffix.lower()

            if suffix in (".yaml", ".yml"):
                yaml_spec = importlib.util.find_spec("yaml")
                if yaml_spec:
                    yaml = importlib.import_module("yaml")
                    payload = yaml.safe_load(content) or {}
                else:
                    payload = self._fallback_yaml_load(content)
            elif suffix == ".json":
                try:
                    payload = json.loads(content) or {}
                except json.JSONDecodeError:  # pragma: no cover
                    payload = {}

        if Draft7Validator and payload:
            Draft7Validator(_SCHEMA).validate(payload)

        servers: List[RegistryServer] = []
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

    @staticmethod
    def _fallback_yaml_load(content: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        current_key: str | None = None
        items: list[Dict[str, Any]] = []
        current_item: Dict[str, Any] = {}

        for line in content.splitlines():
            if not line.strip():
                continue
            if not line.startswith(" "):
                if current_item:
                    items.append(current_item)
                    current_item = {}
                key, _, value = line.partition(":")
                if value.strip():
                    payload[key.strip()] = value.strip()
                else:
                    current_key = key.strip()
            else:
                stripped = line.strip()
                if stripped.startswith("-"):
                    if current_item:
                        items.append(current_item)
                    current_item = {}
                    stripped = stripped.lstrip("-").strip()
                    if stripped:
                        k, _, v = stripped.partition(":")
                        current_item[k.strip()] = v.strip()
                else:
                    k, _, v = stripped.partition(":")
                    current_item[k.strip()] = v.strip()

        if current_item:
            items.append(current_item)
        if current_key and items:
            payload[current_key] = items
        return payload


class ToolRegistry:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.data = RegistryLoader(self.path)._load()

    def enabled(self) -> Iterable[RegistryServer]:
        return [s for s in self.data if s.enabled]


__all__ = ["RegistryLoader", "ToolRegistry", "RegistryServer"]
