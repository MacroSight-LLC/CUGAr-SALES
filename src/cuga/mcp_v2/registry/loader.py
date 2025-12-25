"""YAML-driven MCP registry loader (vertical slice)."""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

import yaml

from .errors import RegistryLoadError, RegistryMergeError, RegistryValidationError
from .models import MCPServerDefinition, MCPToolDefinition
from .snapshot import RegistrySnapshot

ENV_REGISTRY_PATH = "CUGA_MCP_REGISTRY_PATH"
_BOOL_TRUE = {"1", "true", "yes", "on"}


def _coerce_bool(value: Any, *, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _BOOL_TRUE
    raise RegistryValidationError(f"Expected boolean or string flag, got {type(value).__name__}")


def _env_enabled(entry: Mapping[str, Any], env: Mapping[str, str], *, default: bool = True) -> bool:
    enabled = _coerce_bool(entry.get("enabled"), default=default)
    env_key = entry.get("enabled_env")
    if env_key is None:
        return enabled
    env_val = env.get(env_key)
    if env_val is None:
        return False
    return env_val.strip().lower() in _BOOL_TRUE


def _load_yaml(path: Path) -> MutableMapping[str, Any]:
    if not path.exists():
        raise RegistryLoadError(f"Registry file not found: {path}")
    try:
        document = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise RegistryValidationError(f"Invalid YAML in {path}: {exc}") from exc
    if document is None:
        return {}
    if not isinstance(document, MutableMapping):
        raise RegistryValidationError(f"Registry at {path} must be a mapping")
    return document


def _parse_fragments(document: Mapping[str, Any], base_path: Path) -> Sequence[Path]:
    fragments = document.get("fragments", [])
    if fragments is None:
        return []
    if not isinstance(fragments, Sequence) or isinstance(fragments, (str, bytes)):
        raise RegistryValidationError("fragments must be a list of file paths")
    resolved: list[Path] = []
    for fragment in fragments:
        if not isinstance(fragment, str):
            raise RegistryValidationError("fragment entries must be strings")
        resolved.append((base_path.parent / fragment).resolve())
    return resolved


def _resolve_documents(entry_path: Path, *, seen: set[Path] | None = None) -> list[tuple[Path, MutableMapping[str, Any]]]:
    seen = seen or set()
    if entry_path in seen:
        raise RegistryMergeError(f"Cycle detected while loading registry fragments: {entry_path}")
    seen.add(entry_path)
    document = _load_yaml(entry_path)
    docs: list[tuple[Path, MutableMapping[str, Any]]] = [(entry_path, document)]
    for fragment_path in _parse_fragments(document, entry_path):
        docs.extend(_resolve_documents(fragment_path, seen=seen))
    return docs


def _parse_tool(name: str, raw: Mapping[str, Any], env: Mapping[str, str]) -> MCPToolDefinition:
    if not isinstance(raw, Mapping):
        raise RegistryValidationError(f"Tool '{name}' must be a mapping")
    enabled = _env_enabled(raw, env)
    operation_id = raw.get("operation_id")
    method = raw.get("method")
    path = raw.get("path")
    if operation_id is None and (method is None or path is None):
        raise RegistryValidationError(
            f"Tool '{name}' must provide an operation_id or both method and path",
        )
    return MCPToolDefinition(
        name=name,
        description=raw.get("description"),
        operation_id=operation_id,
        method=method.upper() if isinstance(method, str) else method,
        path=path,
        schema=raw.get("schema"),
        enabled=enabled,
        enabled_env=raw.get("enabled_env"),
    )


def _parse_server(name: str, raw: Mapping[str, Any], env: Mapping[str, str]) -> MCPServerDefinition:
    if not isinstance(raw, Mapping):
        raise RegistryValidationError(f"Server '{name}' must be a mapping")
    enabled = _env_enabled(raw, env)
    url = raw.get("url")
    if not isinstance(url, str) or not url.strip():
        raise RegistryValidationError(f"Server '{name}' must declare a non-empty url")
    tools_raw = raw.get("tools", [])
    if tools_raw is None:
        tools_raw = []
    if not isinstance(tools_raw, Sequence) or isinstance(tools_raw, (str, bytes)):
        raise RegistryValidationError(f"Server '{name}' tools must be a list")
    parsed_tools = tuple(
        _parse_tool(
            tool.get("name", f"{name}:{idx}") if isinstance(tool, Mapping) else f"{name}:{idx}",
            tool,
            env,
        )
        for idx, tool in enumerate(tools_raw)
    )
    return MCPServerDefinition(
        name=name,
        url=url,
        schema=raw.get("schema"),
        enabled=enabled,
        enabled_env=raw.get("enabled_env"),
        tools=tuple(tool for tool in parsed_tools if tool.enabled),
    )


def _merge_servers(documents: Iterable[tuple[Path, Mapping[str, Any]]], env: Mapping[str, str]) -> tuple[MCPServerDefinition, ...]:
    merged: list[MCPServerDefinition] = []
    seen: dict[str, Path] = {}
    for source_path, document in documents:
        servers_block = document.get("servers", {})
        if servers_block is None:
            continue
        if not isinstance(servers_block, Mapping):
            raise RegistryValidationError(f"servers block in {source_path} must be a mapping")
        for name, raw_server in servers_block.items():
            if name in seen:
                raise RegistryMergeError(
                    f"Duplicate server '{name}' in {source_path} conflicts with entry from {seen[name]}",
                )
            server = _parse_server(name, raw_server, env)
            if server.enabled:
                merged.append(server)
            seen[name] = source_path
    return tuple(merged)


def load_mcp_registry_snapshot(
    path: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> RegistrySnapshot:
    """Load and validate an MCP registry snapshot.

    No network access or runtime bindings are performed in this slice.
    """

    env = env or os.environ
    raw_path = path if path is not None else env.get(ENV_REGISTRY_PATH)
    if not raw_path:
        return RegistrySnapshot.empty()
    resolved_path = Path(raw_path).expanduser().resolve()
    documents = _resolve_documents(resolved_path)
    servers = _merge_servers(copy.deepcopy(documents), env)
    sources = tuple(path for path, _ in documents)
    return RegistrySnapshot(servers=servers, sources=sources)


__all__ = [
    "ENV_REGISTRY_PATH",
    "load_mcp_registry_snapshot",
]
