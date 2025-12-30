import pytest

from cuga.tools.registry import ToolRegistry


def test_registry_schema_validation(tmp_path):
    payload = {"servers": [{"id": "demo", "url": "http://localhost:8000", "rate_limit_per_minute": 10}]}
    path = tmp_path / "mcp.yaml"
    path.write_text("servers:\n  - id: demo\n    url: http://localhost:8000\n    rate_limit_per_minute: 10\n")
    registry = ToolRegistry(path)
    assert registry.enabled()
