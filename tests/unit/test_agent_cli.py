import json
from pathlib import Path

from cuga import agent_cli


PLUGIN_BODY = """
from cuga.agents.registry import ToolRegistry
from cuga.plugins import ToolPlugin


def handler(payload, *, config, context):
    return {"goal": payload.get("goal"), "config": config, "metadata": context.metadata}


class Plugin(ToolPlugin):
    name = "temp"

    def register_tools(self, registry: ToolRegistry) -> None:
        registry.register("cli", "demo", handler, config={"hello": "world"}, cost=0.1, latency=0.1)


plugin = Plugin()
"""


def test_cli_lists_profiles(tmp_path: Path, capsys):
    plugin_path = tmp_path / "cli_plugin.py"
    plugin_path.write_text(PLUGIN_BODY)

    agent_cli.main(["list", "--plugin", str(plugin_path)])
    output = json.loads(capsys.readouterr().out)

    assert output["profiles"] == ["cli"]


def test_cli_runs_and_exports(tmp_path: Path, capsys):
    plugin_path = tmp_path / "cli_plugin.py"
    plugin_path.write_text(PLUGIN_BODY)
    output_file = tmp_path / "result.json"

    agent_cli.main(["run", "demo goal", "--plugin", str(plugin_path), "--profile", "cli"])
    run_payload = json.loads(capsys.readouterr().out)
    assert run_payload["profile"] == "cli"
    assert run_payload["output"]["goal"] == "demo goal"

    agent_cli.main(
        [
            "export",
            "demo goal",
            "--plugin",
            str(plugin_path),
            "--profile",
            "cli",
            "--output",
            str(output_file),
        ]
    )
    assert output_file.exists()
    exported = json.loads(output_file.read_text())
    assert exported["output"]["config"] == {"hello": "world"}
