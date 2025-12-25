import copy
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from cuga.mcp_v2.registry import (
    RegistryMergeError,
    RegistryValidationError,
    load_mcp_registry_snapshot,
)


def test_loads_snapshot_from_yaml(tmp_path: Path) -> None:
    registry_file = tmp_path / "registry.yaml"
    registry_file.write_text(
        """
servers:
  echo:
    url: http://localhost:9999
    tools:
      - name: echo
        method: post
        path: /echo
        description: Echo payloads
        enabled: true
"""
    )

    snapshot = load_mcp_registry_snapshot(registry_file)

    assert snapshot.sources == (registry_file.resolve(),)
    assert len(snapshot.servers) == 1
    server = snapshot.servers[0]
    assert server.name == "echo"
    assert server.url == "http://localhost:9999"
    assert server.tools[0].method == "POST"

    with pytest.raises(FrozenInstanceError):
        server.name = "mutated"  # type: ignore[misc]


def test_merge_is_deterministic_with_fragments(tmp_path: Path) -> None:
    fragment_one = tmp_path / "fragment_one.yaml"
    fragment_two = tmp_path / "fragment_two.yaml"
    base = tmp_path / "registry.yaml"

    fragment_one.write_text(
        """
servers:
  files:
    url: http://files.example
    tools:
      - name: list_files
        operation_id: listFiles
"""
    )

    fragment_two.write_text(
        """
servers:
  search:
    url: http://search.example
    tools:
      - name: search_web
        method: get
        path: /search
"""
    )

    base.write_text(
        f"""
fragments:
  - {fragment_one.name}
  - {fragment_two.name}
servers:
  echo:
    url: http://echo.example
    tools:
      - name: echo
        method: post
        path: /echo
"""
    )

    snapshot_one = load_mcp_registry_snapshot(base)
    snapshot_two = load_mcp_registry_snapshot(copy.deepcopy(base))

    assert [server.name for server in snapshot_one.servers] == ["echo", "files", "search"]
    assert snapshot_one == snapshot_two
    assert snapshot_one.sources[0] == base.resolve()


def test_conflicting_server_names_raise(tmp_path: Path) -> None:
    fragment = tmp_path / "fragment.yaml"
    base = tmp_path / "registry.yaml"

    fragment.write_text(
        """
servers:
  echo:
    url: http://other-host
    tools:
      - name: alt_echo
        method: post
        path: /alt
"""
    )

    base.write_text(
        f"""
fragments:
  - {fragment.name}
servers:
  echo:
    url: http://original-host
    tools:
      - name: echo
        method: post
        path: /echo
"""
    )

    with pytest.raises(RegistryMergeError):
        load_mcp_registry_snapshot(base)


def test_validation_failure_on_missing_url(tmp_path: Path) -> None:
    registry_file = tmp_path / "registry.yaml"
    registry_file.write_text(
        """
servers:
  incomplete:
    tools:
      - name: noop
        operation_id: noop
"""
    )

    with pytest.raises(RegistryValidationError):
        load_mcp_registry_snapshot(registry_file)
