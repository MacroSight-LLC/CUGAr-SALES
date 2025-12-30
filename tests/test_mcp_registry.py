from pathlib import Path

from cuga.tools.registry import RegistryLoader


def test_load_yaml_registry(tmp_path: Path):
    p = tmp_path / "mcp_servers.yaml"
    p.write_text("servers:\n  - id: a\n    url: http://localhost:8000\n", encoding="utf-8")
    servers = RegistryLoader(p)._load()
    assert len(servers) == 1 and servers[0].id == "a"


def test_load_json_registry(tmp_path: Path):
    p = tmp_path / "mcp_servers.json"
    p.write_text('{"servers":[{"id":"b","url":"https://example"}]}', encoding="utf-8")
    servers = RegistryLoader(p)._load()
    assert len(servers) == 1 and servers[0].id == "b"
