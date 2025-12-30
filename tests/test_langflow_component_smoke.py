import importlib
import importlib.util

import pytest


def test_guard_components_importable():
    if importlib.util.find_spec("lfx") is None:
        pytest.skip("Langflow optional dependency is not installed")

    modules = [
        "cuga.langflow_components.guard_input",
        "cuga.langflow_components.guard_tool",
        "cuga.langflow_components.guard_output",
        "cuga.langflow_components.guard_orchestrator",
    ]
    for mod in modules:
        assert importlib.import_module(mod)
