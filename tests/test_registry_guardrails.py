from __future__ import annotations

from pathlib import Path

import pytest

from cuga.backend.app import registry_path
from cuga.observability import InMemoryTracer
from cuga.registry.loader import ALLOWED_SANDBOXES, Registry


def test_registry_enforces_sandboxes_and_exec_mounts():
    registry = Registry(registry_path)
    exec_entries = [entry for entry in registry.entries if "exec" in entry.scopes]
    assert exec_entries, "exec-scoped entries should be present for coverage"
    assert all(entry.sandbox in ALLOWED_SANDBOXES for entry in registry.entries)
    assert all(any(mount.startswith("/workdir") for mount in entry.mounts) for entry in exec_entries)


def test_registry_budget_policy_and_env_defaults(tmp_path: Path):
    registry = Registry(registry_path)
    assert all("AGENT_BUDGET_CEILING" in entry.env for entry in registry.entries)
    assert all(entry.budget_policy in {"warn", "block"} for entry in registry.entries)

    invalid = tmp_path / "bad.yaml"
    invalid.write_text(
        """
version: v1
defaults: {tier: 1, sandbox: py-slim}
entries:
  - id: bad
    ref: docker://bad
    sandbox: custom
"""
    )

    with pytest.raises(ValueError):
        Registry(invalid)


def test_hot_reload_records_traces_and_ordering():
    tracer = InMemoryTracer()
    registry = Registry(registry_path, tracer=tracer)
    registry.hot_reload(
        """
version: v1
defaults: {tier: 1, enabled: true, sandbox: py-slim, budget_policy: warn}
entries:
  - id: b
    ref: docker://b
    scopes: [exec]
    mounts: [/workdir:ro]
  - id: a
    ref: docker://a
    scopes: [exec]
    mounts: [/workdir:ro]
"""
    )
    assert [entry.id for entry in registry.entries] == ["a", "b"]
    assert tracer.spans
    assert tracer.spans[-1].attributes.get("count") == 2
