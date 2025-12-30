from pathlib import Path

from cuga.tools.registry import RegistryLoader


def test_invalid_schema_returns_empty(tmp_path: Path):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text('{"servers": {"id": "bad"}}', encoding="utf-8")

    loader = RegistryLoader(registry_path)
    assert loader._load() == []


def test_missing_fields_skipped(tmp_path: Path):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        """
        {"servers": [
            {"id": "valid", "url": "http://ok"},
            {"id": "missing-url"},
            "not-a-dict"
        ]}
        """.strip(),
        encoding="utf-8",
    )

    loader = RegistryLoader(registry_path)
    servers = loader._load()

    assert len(servers) == 1
    assert servers[0].id == "valid"
    assert servers[0].url == "http://ok"
