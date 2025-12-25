import json
from pathlib import Path

from cuga.agents.registry import ToolRegistry
from cuga.plugins import discover_plugins, load_plugins


PLUGIN_BODY = """
from cuga.agents.registry import ToolRegistry
from cuga.plugins import ToolPlugin


def handler(payload, *, config, context):
    return {"goal": payload.get("goal"), "config": config, "meta": context.metadata}


class Plugin(ToolPlugin):
    name = "temp"

    def register_tools(self, registry: ToolRegistry) -> None:
        registry.register("test", "demo", handler, config={"value": 1}, cost=0.2, latency=0.2)


plugin = Plugin()
"""


def test_load_plugins_from_path(tmp_path: Path):
    plugin_path = tmp_path / "temp_plugin.py"
    plugin_path.write_text(PLUGIN_BODY)

    registry = ToolRegistry()
    results = load_plugins(registry, [str(plugin_path)])

    assert results[0].loaded
    resolved = registry.resolve("test", "demo")
    assert resolved["config"]["value"] == 1
    assert resolved["cost"] == 0.2


def test_discover_plugins_reports_errors(tmp_path: Path):
    bad_path = tmp_path / "bad.py"
    bad_path.write_text("broken = True")

    results = discover_plugins([str(bad_path)])
    assert results[0].plugin is None
    assert results[0].error is not None
